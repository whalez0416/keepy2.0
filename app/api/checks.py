from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.homepage_checker import check_homepage
from ..services.form_checker import check_form
from ..services.alert_service import handle_check_result
from .auth import get_current_user, require_org_writer

router = APIRouter(tags=["checks"])

@router.post("/run/{site_id}")
def run_manual_check(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)
        
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")

    # 수동 점검은 자원을 쓰는 동작이므로 쓰기 권한 보유자만 허용(VIEWER 차단)
    require_org_writer(db, current_user, site.org_id)

    # Run homepage check
    h_log = check_homepage(db, site)
    if h_log:
        handle_check_result(db, site, "homepage", h_log.status, h_log.fail_reason)

    # Run form checks
    form_results = []
    for f_config in site.form_configs:
        f_log = check_form(db, f_config)
        if f_log:
            # 스케줄러와 동일한 키("form:<폼이름>")로 넘겨 쿨다운/알림 식별을 일치시킨다
            handle_check_result(db, site, f"form:{f_config.name}", f_log.status, f_log.fail_reason)
            form_results.append({"name": f_config.name, "status": f_log.status})

    # Run visual defacement check (변조 의심 warning만 알림; fail=시스템 오류는 제외)
    from ..services.visual_checker import check_visual_defacement
    v_log = check_visual_defacement(db, site)
    if v_log and v_log.status == "warning":
        handle_check_result(db, site, "visual_defacement", v_log.status, v_log.fail_reason)

    # Run contact hijack check
    from ..services.contact_checker import check_contact
    c_results = []
    for c_config in site.contact_configs:
        c_log = check_contact(db, c_config)
        if c_log:
            handle_check_result(db, site, "contact_hijack", c_log.status, c_log.fail_reason)
            c_results.append({"id": c_config.id, "status": c_log.status})

    # Run SSL check
    from ..services.ssl_service import check_and_renew_ssl
    ssl_result = check_and_renew_ssl(db, site)
    if ssl_result:
        ssl_status, ssl_message = ssl_result
        handle_check_result(db, site, "ssl", ssl_status, ssl_message)

    return {
        "homepage": h_log.status if h_log else "skipped",
        "forms": form_results,
        "visual": v_log.status if v_log else "skipped",
        "contacts": c_results,
        "ssl": ssl_result[0] if ssl_result else "ok",
    }
