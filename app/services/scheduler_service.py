from sqlalchemy.orm import Session
from ..scheduler import scheduler
from ..models import Site
from .homepage_checker import check_homepage
from .form_checker import check_form
from .spam_hunter import run_spam_hunter
from .alert_service import handle_check_result
from ..db import SessionLocal
from ..utils.logger import get_logger

logger = get_logger("scheduler_service")

def run_site_check(site_id: int, check_type: str):
    db: Session = SessionLocal()
    try:
        site = db.query(Site).get(site_id)
        if not site or not site.is_active:
            return

        if check_type == "homepage":
            log = check_homepage(db, site)
        elif check_type == "form":
            log = check_form(db, site)
        elif check_type == "spam":
            for config in site.spam_configs:
                run_spam_hunter(db, config)
            log = None # 스팸 헌터는 별도의 로그 처리가 필요할 수 있음
            
        if log:
            handle_check_result(db, site, check_type, log.status, log.fail_reason)
            
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
    
    # 상담폼 체크 작업 추가
    if site.form_url:
        scheduler.add_job(
            run_site_check,
            'interval',
            minutes=site.form_check_interval_minutes,
            args=[site.id, "form"],
            id=f"site_{site.id}_form"
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
    for job_id in [f"site_{site_id}_homepage", f"site_{site_id}_form", f"site_{site_id}_spam"]:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

def init_all_jobs():
    db = SessionLocal()
    active_sites = db.query(Site).filter(Site.is_active == True).all()
    for site in active_sites:
        update_site_jobs(site)
    db.close()
    logger.debug(f"활성 상태인 {len(active_sites)}개 사이트의 작업 초기화 완료")
