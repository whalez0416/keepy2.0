import requests
import time
from sqlalchemy.orm import Session
from ..models import Site, Log, Alert
from ..utils.logger import get_logger
import ssl
import socket
from datetime import datetime

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
        
        # SSL 체크 추가
        ssl_status = "success"
        if site.homepage_url.startswith("https"):
            try:
                hostname = site.homepage_url.split("//")[1].split("/")[0]
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        # cert['notAfter'] format: 'Mar 15 14:00:00 2026 GMT'
                        expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                        days_left = (expire_date - datetime.now()).days
                        
                        if days_left < 7:
                            ssl_status = "danger"
                            status = "fail"
                            fail_reason = f"SSL 인증서 만료 임박 ({days_left}일 남음)"
                        elif days_left < 30:
                            ssl_status = "warning"
                            if status == "success": # 다른 장애가 없다면 warning으로 표시
                                status = "warning"
                                fail_reason = f"SSL 인증서 만료 예고 ({days_left}일 남음)"
            except Exception as se:
                logger.error(f"SSL 체크 실패: {se}")
                ssl_status = "fail"

        if response_time > 3.0 and status == "success":
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
