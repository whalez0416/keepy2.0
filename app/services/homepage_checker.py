import requests
import time
from sqlalchemy.orm import Session
from ..models import Site, Log
from ..utils.logger import get_logger

logger = get_logger("homepage_checker")

def check_homepage(db: Session, site: Site):
    logger.debug(f"홈페이지 체크 시작: site_id={site.id} url={site.homepage_url}")
    
    start_time = time.time()
    try:
        response = requests.get(site.homepage_url, timeout=10)
        response_time = time.time() - start_time
        
        status = "success"
        fail_reason = None
        
        if response.status_code >= 400:
            status = "fail"
            fail_reason = f"HTTP {response.status_code}"
        elif response_time > 3.0:
            status = "warning"
            fail_reason = f"응답 지연: {response_time:.2f}s"
            
        logger.debug(f"홈페이지 체크 {status}: site_id={site.id} response_time={response_time:.2f}")
        
    except Exception as e:
        response_time = time.time() - start_time
        status = "fail"
        fail_reason = str(e)
        logger.debug(f"홈페이지 체크 실패: site_id={site.id} 사유={fail_reason}")

    log = Log(
        site_id=site.id,
        check_type="homepage",
        status=status,
        response_time=response_time,
        fail_reason=fail_reason,
        raw_result=None
    )
    db.add(log)
    db.commit()
    return log
