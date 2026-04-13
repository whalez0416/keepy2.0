import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("email_service")

def send_alert_email(site_name: str, check_type: str, status: str, fail_reason: str, checked_at: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP 설정이 구성되지 않았습니다. 이메일 알림을 건너뜁니다.")
        return False
        
    subject = f"[{settings.APP_NAME}] {site_name} - {check_type.upper()} {status.upper()} 장애 알림"
    
    body = f"""
    Keepy MVP 모니터링 알림
    
    사이트명: {site_name}
    점검 유형: {check_type}
    상태: {status}
    발생 시간: {checked_at}
    실패 사유: {fail_reason}
    
    사이트 상태를 즉시 확인해 주시기 바랍니다.
    """
    
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_FROM_EMAIL
    msg['To'] = settings.SMTP_USER # 관리자에게 전송 (MVP 단순화)
    msg['Subject'] = Header(subject, 'utf-8')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.debug(f"알림 이메일 발송 성공: site_name={site_name}")
        return True
    except Exception as e:
        logger.error(f"알림 이메일 발송 실패: {str(e)}")
        return False
