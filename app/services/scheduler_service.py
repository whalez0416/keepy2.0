import os
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..scheduler import scheduler
from ..config import settings
from ..models import Site, FormConfig, Log
from .homepage_checker import check_homepage
from .form_checker import check_form
from .ai_spam_classifier import run_ai_spam_hunter
from .contact_checker import check_contact
from .ssl_service import check_and_renew_ssl
from .visual_checker import check_visual_defacement
from .admin_watcher import check_admin_exposure
from .alert_service import handle_check_result
from ..db import SessionLocal
from ..utils.logger import get_logger

logger = get_logger("scheduler_service")

def run_site_check(site_id: int, check_type: str, extra_id: int = None):
    db: Session = SessionLocal()
    try:
        site = db.query(Site).get(site_id)
        if not site or not site.is_active:
            return

        log = None
        if check_type == "homepage":
            log = check_homepage(db, site)
            if log:
                handle_check_result(db, site, "homepage", log.status, log.fail_reason)
                # NOTE: 과거엔 '연속 5회 실패 시 자동 비활성화'가 있었으나 제거함.
                # 장기 장애야말로 고객이 알림받길 원하는 상황인데, 감시를 통째로 꺼버리면
                # 복구도 감지 못 하고 침묵하게 된다. 반복 알림은 handle_check_result의
                # '미해결 동안 1회만' 중복억제가 막으므로, 감시는 계속 유지한다.

        elif check_type == "form":
            form_config = db.query(FormConfig).get(extra_id)
            if form_config and form_config.is_active:
                log = check_form(db, form_config)
                if log:
                    handle_check_result(db, site, f"form:{form_config.name}", log.status, log.fail_reason)
        
        elif check_type == "spam":
            for config in site.spam_configs:
                if not config.is_active:
                    continue
                result = run_ai_spam_hunter(db, config)
                # 스팸이 탐지되면 알림 생성 (탐지 + 알림, 자동 삭제는 안 함)
                if result and result.get("spam_detected", 0) > 0:
                    titles = ", ".join(
                        p.get("title", "")[:30] for p in result.get("spam_posts", [])[:5]
                    )
                    msg = (
                        f"🚫 [스팸 탐지] {site.site_name} 게시판에서 의심 게시물 "
                        f"{result['spam_detected']}건이 발견되었습니다. (예: {titles})"
                    )
                    handle_check_result(db, site, "spam", "warning", msg)
        
        elif check_type == "contact":
            for config in site.contact_configs:
                if config.is_active:
                    log = check_contact(db, config)
                    if log:
                        handle_check_result(db, site, "contact_hijack", log.status, log.fail_reason)
        
        elif check_type == "ssl_renewal":
            result = check_and_renew_ssl(db, site)
            if result:
                status, message = result
                handle_check_result(db, site, "ssl", status, message)

        elif check_type == "visual":
            log = check_visual_defacement(db, site)
            # status=="warning"만 '변조 의심'. "fail"은 브라우저/네트워크 시스템 오류이므로
            # 고객에게 변조로 잘못 알리지 않는다.
            if log and log.status == "warning":
                handle_check_result(db, site, "visual_defacement", log.status, log.fail_reason)
            
        elif check_type == "admin_watch":
            log = check_admin_exposure(db, site)
            # warning(무인증 노출 의심)만 알림. fail(시스템 오류)은 제외.
            if log and log.status == "warning":
                handle_check_result(db, site, "admin_exposure", "warning", log.fail_reason)
            
    except Exception as e:
        logger.error(f"예약된 점검 실행 중 오류 발생: {str(e)}")
    finally:
        db.close()

def update_site_jobs(site: Site):
    # 해당 사이트의 기존 작업 제거
    remove_site_jobs(site.id)
    
    if not site.is_active:
        return

    # 홈페이지 체크 작업 추가
    scheduler.add_job(
        run_site_check,
        'interval',
        minutes=site.check_interval_minutes,
        args=[site.id, "homepage"],
        id=f"site_{site.id}_homepage"
    )
    
    # 여러 상담폼 체크 작업 추가
    for form in site.form_configs:
        if form.is_active:
            scheduler.add_job(
                run_site_check,
                'interval',
                minutes=form.check_interval_minutes,
                args=[site.id, "form", form.id],
                id=f"site_{site.id}_form_{form.id}"
            )
    
    # 스팸 헌터 작업 추가 (예: 6시간마다)
    if site.spam_configs:
        scheduler.add_job(
            run_site_check,
            'interval',
            hours=6,
            args=[site.id, "spam"],
            id=f"site_{site.id}_spam"
        )
    
    # 연락처 변조 체크 작업 추가 (기본 1시간)
    if site.contact_configs:
        scheduler.add_job(
            run_site_check,
            'interval',
            minutes=60,
            args=[site.id, "contact"],
            id=f"site_{site.id}_contact"
        )
    
    # SSL 자동 연장 체크 (매일 새벽 3시)
    scheduler.add_job(
        run_site_check,
        'cron',
        hour=3,
        minute=0,
        args=[site.id, "ssl_renewal"],
        id=f"site_{site.id}_ssl_renewal"
    )
    
    # 비주얼 변조 체크 (매일 새벽 4시 - 무거운 작업이므로 빈도 낮게)
    scheduler.add_job(
        run_site_check,
        'cron',
        hour=4,
        minute=0,
        args=[site.id, "visual"],
        id=f"site_{site.id}_visual"
    )
    
    # 관리자 페이지 감시 (6시간마다)
    scheduler.add_job(
        run_site_check,
        'interval',
        hours=6,
        args=[site.id, "admin_watch"],
        id=f"site_{site.id}_admin_watch"
    )
    
    logger.debug(f"사이트 작업 업데이트 완료: site_id={site.id}")

def remove_site_jobs(site_id: int):
    # 등록된 모든 관련 작업 제거 (와일드카드 패턴 검색이 안 되므로 명시적으로 제거하거나 필터링 필요)
    # 여기서는 간단히 기존 ID 패턴들을 처리
    all_jobs = scheduler.get_jobs()
    for job in all_jobs:
        if job.id.startswith(f"site_{site_id}_"):
            scheduler.remove_job(job.id)

def cleanup_old_screenshots():
    """보존기간(SCREENSHOT_RETENTION_DAYS)이 지난 점검 스크린샷을 삭제한다.

    파일은 mtime 기준으로 지우고, 만료된 로그의 screenshot_path도 비워(끊긴 이미지
    링크 방지) 둔다. 보관이 필요한 스크린샷은 사용자가 미리 다운로드해 따로 보관한다.
    """
    retention = settings.SCREENSHOT_RETENTION_DAYS
    cutoff_ts = time.time() - retention * 86400
    screenshot_dir = os.path.join("app", "static", "screenshots")
    removed = 0
    if os.path.isdir(screenshot_dir):
        for fn in os.listdir(screenshot_dir):
            fp = os.path.join(screenshot_dir, fn)
            try:
                if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff_ts:
                    os.remove(fp)
                    removed += 1
            except OSError:
                pass

    db = SessionLocal()
    try:
        cutoff_dt = datetime.utcnow() - timedelta(days=retention)
        db.query(Log).filter(
            Log.checked_at < cutoff_dt,
            Log.screenshot_path.isnot(None),
        ).update({Log.screenshot_path: None}, synchronize_session=False)
        db.commit()
    except Exception as e:
        logger.error(f"스크린샷 로그 경로 정리 중 오류: {e}")
    finally:
        db.close()
    logger.info(f"[정리] 보존 {retention}일 초과 스크린샷 {removed}개 삭제 완료")


def init_all_jobs():
    db = SessionLocal()
    active_sites = db.query(Site).filter(Site.is_active == True).all()
    for site in active_sites:
        update_site_jobs(site)
    db.close()

    # 전역(사이트 무관) 작업: 스크린샷 자동 정리 — 매일 새벽 5시 30분
    scheduler.add_job(
        cleanup_old_screenshots,
        'cron',
        hour=5,
        minute=30,
        id="global_screenshot_cleanup",
        replace_existing=True,
    )

    logger.debug(f"활성 상태인 {len(active_sites)}개 사이트의 작업 초기화 완료")
