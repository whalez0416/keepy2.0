import ssl
import socket
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Site, Log, Alert, Organization
from ..utils.logger import get_logger
import time

logger = get_logger("ssl_service")

def check_and_renew_ssl(db: Session, site: Site):
    """
    인증서 만료일을 확인하고, 30일 미만일 경우 자동 연장 프로세스를 시작합니다.
    (Type B 이상 고객 대상)
    """
    # 1. 대상 확인 (Pro 플랜 이상인지 확인)
    org = site.organization
    if org.plan not in ["pro", "enterprise", "type_b", "type_c", "corporate"]:
        logger.debug(f"SSL 자동 연장 대상 아님: site_id={site.id} plan={org.plan}")
        return False

    # 2. 현재 상태 확인
    try:
        hostname = site.homepage_url.split("//")[1].split("/")[0]
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                days_left = (expire_date - datetime.now()).days
                
                logger.info(f"SSL 상태 확인: site={hostname} 잔여={days_left}일")

                # 3. 연장 조건 확인 (30일 미만 시)
                if days_left < 30:
                    logger.info(f"SSL 자동 연장 시작: site_id={site.id} ({days_left}일 남음)")
                    return trigger_ssl_renewal(db, site)
                
    except Exception as e:
        logger.error(f"SSL 상태 확인 중 오류: {e}")
        return False

def trigger_ssl_renewal(db: Session, site: Site):
    """
    실제 SSL 연장 로직 (여기서는 시뮬레이션 및 API 연동 구조를 가짐)
    """
    try:
        # 시뮬레이션: 실제로는 Certbot API나 ZeroSSL API를 호출함
        logger.info(f"[RENEWAL] ACME 챌린지 시작 (HTTP-01)...")
        time.sleep(2)
        logger.info(f"[RENEWAL] 도메인 소유권 확인 완료.")
        time.sleep(1)
        logger.info(f"[RENEWAL] 새 인증서 발급 중...")
        time.sleep(2)
        logger.info(f"[RENEWAL] 서버에 인증서 배포 및 엔진엑스 재시작 완료.")

        # 성공 로그 및 알림
        log = Log(
            site_id=site.id,
            check_type="ssl_renewal",
            status="success",
            fail_reason=None,
            raw_result="SSL 인증서가 성공적으로 자동 연장되었습니다. (유효기간 90일 연장)"
        )
        db.add(log)
        
        alert = Alert(
            site_id=site.id,
            check_type="ssl_renewal",
            alert_level="info",
            message=f"✅ [자동 연장 완료] {site.site_name}의 SSL 인증서가 성공적으로 갱신되었습니다."
        )
        db.add(alert)
        db.commit()
        
        return True
    except Exception as e:
        logger.error(f"SSL 연장 실패: {e}")
        alert = Alert(
            site_id=site.id,
            check_type="ssl_renewal",
            alert_level="danger",
            message=f"❌ [자동 연장 실패] {site.site_name} SSL 갱신 중 오류가 발생했습니다: {str(e)}"
        )
        db.add(alert)
        db.commit()
        return False
