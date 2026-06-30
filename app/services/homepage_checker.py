import requests
import time
from sqlalchemy.orm import Session
from ..models import Site, Log, Alert
from ..utils.logger import get_logger
from ..utils.url_guard import safe_get
import ssl
import socket
from datetime import datetime

logger = get_logger("homepage_checker")

# 일부 병원 사이트는 WAF/CDN이 기본 python-requests UA를 403으로 막아 정상 사이트를
# 장애로 오탐할 수 있다. 실제 브라우저처럼 보이게 헤더를 설정한다.
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

def check_homepage(db: Session, site: Site):
    logger.debug(f"홈페이지 체크 시작: site_id={site.id} url={site.homepage_url}")

    start_time = time.time()
    try:
        # SSRF 안전 fetch: 요청 직전 호스트 재해석 + 리다이렉트 각 홉 재검증(내부주소 우회 차단)
        response = safe_get(site.homepage_url, timeout=10, headers=_BROWSER_HEADERS)
        response_time = time.time() - start_time
        
        status = "success"
        fail_reason = None

        if response.status_code >= 400:
            status = "fail"
            fail_reason = f"HTTP {response.status_code}"
        else:
            # 호스팅/도메인 만료 시 흔히 200을 반환하는 '정지/주차 페이지'를 다운으로 잡는다.
            # (HTTP 200이라 상태코드만 보면 정상으로 오인되는 가장 흔한 실제 장애 유형)
            low = (response.text or "").lower()
            _DOWN_SIGNALS = [
                "계정이 정지", "계정은 정지", "서비스가 정지", "이용이 정지", "정지되었습니다",
                "도메인이 만료", "도메인 만료", "호스팅 만료", "서비스 기간이 만료", "만료되었습니다",
                "구매가 가능한 도메인", "도메인 주차", "account suspended",
                "this domain is parked", "domain is for sale", "this account has been suspended",
            ]
            if any(s in low or s in (response.text or "") for s in _DOWN_SIGNALS):
                status = "fail"
                fail_reason = "사이트가 정지/만료(주차) 페이지로 보입니다 — 호스팅·도메인 상태 확인 필요"
        
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
