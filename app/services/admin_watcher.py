import requests
import time
from sqlalchemy.orm import Session
from ..models import Site, Log, Alert
from ..utils.logger import get_logger

logger = get_logger("admin_watcher")

def check_admin_exposure(db: Session, site: Site):
    """
    관리자 페이지가 외부에 공개되어 있는지(보안 취약점) 감시합니다.
    (Corporate 플랜 대상)
    """
    if not site.admin_path:
        return None

    # URL 구성 (예: http://hospital.com/admin)
    base_url = site.homepage_url.rstrip('/')
    admin_url = f"{base_url}/{site.admin_path.lstrip('/')}"
    
    logger.debug(f"관리자 페이지 노출 체크 시작: {admin_url}")
    
    start_time = time.time()
    status = "success"
    fail_reason = None
    is_exposed = False

    try:
        # User-Agent를 일반 브라우저처럼 설정
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        response = requests.get(admin_url, headers=headers, timeout=10, allow_redirects=True)
        
        # 200 OK이거나 로그인 폼이 보인다면 노출된 것으로 판단
        if response.status_code == 200:
            is_exposed = True
            status = "warning"
            fail_reason = "관리자 페이지가 외부에 공개되어 있습니다. (IP 제한 필요)"
        
        elif response.status_code == 403:
            # 403 Forbidden이면 IP 제한이 잘 되어 있는 것임
            is_exposed = False
            status = "success"
            logger.debug(f"관리자 페이지 보호 중 (403 Forbidden): {site.id}")
            
    except Exception as e:
        logger.error(f"관리자 페이지 체크 중 오류: {e}")
        status = "fail"
        fail_reason = str(e)

    # 노출 시 긴급 알림 생성
    if is_exposed:
        alert = Alert(
            site_id=site.id,
            check_type="admin_exposure",
            alert_level="danger",
            message=f"🚨 [보안 취약점] 관리자 페이지({site.admin_path})가 보호되지 않고 외부에 노출되어 있습니다! 허용된 IP 외의 접근을 차단하십시오."
        )
        db.add(alert)
        logger.warning(f"ALERT: 관리자 페이지 노출 탐지! site_id={site.id}")

    log = Log(
        site_id=site.id,
        check_type="admin_exposure",
        status=status,
        response_time=time.time() - start_time,
        fail_reason=fail_reason,
        raw_result=f"URL: {admin_url}, Status: {status}"
    )
    db.add(log)
    db.commit()
    
    return log
