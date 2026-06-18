import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("email_service")

def send_alert_email(site_name: str, check_type: str, status: str, fail_reason: str,
                     checked_at: str, recipients=None):
    """장애/변조 알림 이메일을 수신처(고객)에게 발송한다.

    recipients: 고객 조직의 알림 수신 이메일 목록. 비어 있으면 운영자(SMTP_USER)에게
    폴백 발송한다(누락 방지). 과거에는 무조건 SMTP_USER로만 보내 고객이 알림을
    못 받던 문제가 있었다.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP 설정이 구성되지 않았습니다. 이메일 알림을 건너뜁니다.")
        return False

    # 수신처 정리: 공백 제거, 중복 제거. 없으면 운영자에게 폴백.
    to_list = [r.strip() for r in (recipients or []) if r and r.strip()]
    # 순서 보존 중복 제거
    seen = set()
    to_list = [r for r in to_list if not (r in seen or seen.add(r))]
    if not to_list:
        to_list = [settings.SMTP_USER]
        logger.warning(f"수신 이메일 미설정 — 운영자({settings.SMTP_USER})에게 폴백 발송: {site_name}")

    subject = f"[{settings.APP_NAME}] {site_name} - {check_type.upper()} {status.upper()} 알림"

    body = f"""
    Keepy 모니터링 알림

    사이트명: {site_name}
    점검 유형: {check_type}
    상태: {status}
    발생 시간: {checked_at}
    내용: {fail_reason}

    사이트 상태를 즉시 확인해 주시기 바랍니다.
    """

    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_FROM_EMAIL
    msg['To'] = ", ".join(to_list)
    msg['Subject'] = Header(subject, 'utf-8')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.debug(f"알림 이메일 발송 성공: site_name={site_name} 수신={to_list}")
        return True
    except Exception as e:
        logger.error(f"알림 이메일 발송 실패: {str(e)}")
        return False
