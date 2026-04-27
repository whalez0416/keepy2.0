from sqlalchemy.orm import Session
from ..scheduler import scheduler
from ..models import Site, FormConfig
from .homepage_checker import check_homepage
from .form_checker import check_form
from .spam_hunter import run_spam_hunter
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
        
        elif check_type == "form":
            form_config = db.query(FormConfig).get(extra_id)
            if form_config and form_config.is_active:
                log = check_form(db, form_config)
                if log:
                    handle_check_result(db, site, f"form:{form_config.name}", log.status, log.fail_reason)
        
        elif check_type == "spam":
            for config in site.spam_configs:
                run_spam_hunter(db, config)
            
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
    
    logger.debug(f"사이트 작업 업데이트 완료: site_id={site.id}")

def remove_site_jobs(site_id: int):
    # 등록된 모든 관련 작업 제거 (와일드카드 패턴 검색이 안 되므로 명시적으로 제거하거나 필터링 필요)
    # 여기서는 간단히 기존 ID 패턴들을 처리
    all_jobs = scheduler.get_jobs()
    for job in all_jobs:
        if job.id.startswith(f"site_{site_id}_"):
            scheduler.remove_job(job.id)

def init_all_jobs():
    db = SessionLocal()
    active_sites = db.query(Site).filter(Site.is_active == True).all()
    for site in active_sites:
        update_site_jobs(site)
    db.close()
    logger.debug(f"활성 상태인 {len(active_sites)}개 사이트의 작업 초기화 완료")
