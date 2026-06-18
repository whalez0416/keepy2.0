import ssl
import socket
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Site, Log
from ..utils.logger import get_logger

logger = get_logger("ssl_service")

# 만료 며칠 전부터 경고할지
SSL_WARN_DAYS = 30


def check_and_renew_ssl(db: Session, site: Site):
    """
    SSL 인증서 만료일을 확인하고, 만료가 임박(30일 미만)하면 (status, message)를 반환한다.
    정상이거나 점검 불가 시 None을 반환한다. Alert 생성/이메일은 스케줄러가
    handle_check_result로 일원화 처리한다(쿨다운·수신처 일관성).

    주의: 이전 버전은 실제 갱신 없이 'time.sleep' 후 "갱신 완료"라는 거짓 기록을
    남겼다. 실제 인증서 자동 갱신은 고객 서버 접근 권한(ACME/Certbot 연동)이 필요하므로,
    현재는 '만료 모니터링 + 알림'까지만 정직하게 수행한다.
    """
    try:
        hostname = site.homepage_url.split("//")[1].split("/")[0]
    except (IndexError, AttributeError):
        logger.error(f"SSL 점검: 잘못된 URL 형식 site_id={site.id} url={site.homepage_url}")
        return None

    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expire_date - datetime.now()).days

        logger.info(f"SSL 상태 확인: site={hostname} 잔여={days_left}일")

        if days_left < 0:
            return _record(db, site, "fail",
                           f"🚨 [SSL 만료] {site.site_name}의 SSL 인증서가 이미 만료되었습니다. "
                           f"즉시 갱신이 필요합니다.")
        if days_left < SSL_WARN_DAYS:
            return _record(db, site, "warning",
                           f"⚠️ [SSL 만료 임박] {site.site_name}의 SSL 인증서가 {days_left}일 후 만료됩니다. "
                           f"갱신을 준비하세요.")

        # 정상: 기록만 남김
        log = Log(
            site_id=site.id,
            check_type="ssl",
            status="success",
            raw_result=f"SSL 정상 (만료까지 {days_left}일 남음)",
        )
        db.add(log)
        db.commit()
        return None

    except ssl.SSLError as e:
        return _record(db, site, "fail",
                       f"🚨 [SSL 오류] {site.site_name}의 SSL 인증서에 문제가 있습니다: {e}")
    except Exception as e:
        logger.error(f"SSL 상태 확인 중 오류: site_id={site.id} {e}")
        return None


def _record(db: Session, site: Site, status: str, message: str):
    """SSL 점검 결과 로그를 남기고 (status, message)를 반환한다.

    Alert/이메일은 호출측(스케줄러→handle_check_result)에서 생성한다.
    """
    db.add(Log(
        site_id=site.id,
        check_type="ssl",
        status=status,
        fail_reason=message,
        raw_result=message,
    ))
    db.commit()
    return status, message
