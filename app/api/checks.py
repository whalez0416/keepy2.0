from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, SessionLocal
from .. import models
from ..services.homepage_checker import check_homepage
from ..services.form_checker import check_form
from ..services.alert_service import handle_check_result
from ..utils.logger import get_logger
from .auth import get_current_user, require_org_writer

router = APIRouter(tags=["checks"])
logger = get_logger("checks_api")

# 실행 중인 수동 점검(사이트 id). 브라우저 점검이 수 분 걸릴 수 있어, 버튼 연타로
# Chromium이 여러 개 뜨는 것을 막는다.
# ponytail: 인메모리 가드 — 단일 워커 전제(현재 Render 1워커). 워커 늘리면 DB 락 필요.
_running_manual_checks: set = set()


def _run_all_checks(site_id: int):
    """수동 점검 전체 실행(백그라운드). 결과는 로그/알림으로 확인한다."""
    db: Session = SessionLocal()
    try:
        site = db.query(models.Site).get(site_id)
        if not site:
            return

        log = check_homepage(db, site)
        if log:
            handle_check_result(db, site, "homepage", log.status, log.fail_reason)

        for f_config in site.form_configs:
            f_log = check_form(db, f_config)
            if f_log:
                # 스케줄러와 동일한 키("form:<폼이름>")로 넘겨 쿨다운/알림 식별을 일치시킨다
                handle_check_result(db, site, f"form:{f_config.name}", f_log.status, f_log.fail_reason)

        # 변조 의심 warning만 알림; fail=시스템 오류는 제외
        from ..services.visual_checker import check_visual_defacement
        v_log = check_visual_defacement(db, site)
        if v_log and v_log.status == "warning":
            handle_check_result(db, site, "visual_defacement", v_log.status, v_log.fail_reason)

        from ..services.contact_checker import check_contact
        for c_config in site.contact_configs:
            c_log = check_contact(db, c_config)
            if c_log:
                handle_check_result(db, site, "contact_hijack", c_log.status, c_log.fail_reason)

        from ..services.ssl_service import check_and_renew_ssl
        ssl_result = check_and_renew_ssl(db, site)
        if ssl_result:
            ssl_status, ssl_message = ssl_result
            handle_check_result(db, site, "ssl", ssl_status, ssl_message)
    except Exception as e:
        logger.error(f"수동 점검 실행 중 오류: site_id={site_id} {e}")
    finally:
        _running_manual_checks.discard(site_id)
        db.close()


@router.post("/run/{site_id}")
def run_manual_check(site_id: int, background_tasks: BackgroundTasks,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    """수동 점검 시작. 브라우저 점검(폼/화면 등)은 수 분 걸릴 수 있어 요청을 붙잡지 않고
    백그라운드로 돌린다(과거엔 요청 스레드에서 직렬 실행 → 프록시 타임아웃으로
    실패처럼 보이던 문제). 결과는 로그/알림 내역에서 확인."""
    query = db.query(models.Site).filter(models.Site.id == site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)

    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")

    # 수동 점검은 자원을 쓰는 동작이므로 쓰기 권한 보유자만 허용(VIEWER 차단)
    require_org_writer(db, current_user, site.org_id)

    if site.id in _running_manual_checks:
        return {"status": "already_running", "message": "이미 점검이 진행 중입니다. 잠시 후 로그에서 결과를 확인하세요."}

    _running_manual_checks.add(site.id)
    background_tasks.add_task(_run_all_checks, site.id)
    return {"status": "started", "message": "점검을 시작했습니다. 1~2분 후 로그 보기에서 결과를 확인하세요."}
