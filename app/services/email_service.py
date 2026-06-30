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

    # 고객 수신처가 하나도 없으면 운영자에게 폴백한다. 다만 과거엔 이게 '조용히' 일어나
    # 고객은 아무 알림도 못 받는데 시스템은 발송 성공으로 기록하던 위험이 있었다.
    # → 폴백 시 제목/본문에 '수신처 미설정'을 명시해 운영자가 즉시 설정 누락을 알아채게 한다.
    is_operator_fallback = not to_list
    if is_operator_fallback:
        to_list = [settings.SMTP_USER]
        logger.warning(
            f"⚠️ 수신 이메일 미설정 — 고객이 알림을 못 받습니다. 운영자({settings.SMTP_USER})에게 "
            f"폴백 발송: {site_name}. 설정>알림 수신에 고객 이메일을 입력하세요."
        )

    subject = f"[{settings.APP_NAME}] {site_name} - {check_type.upper()} {status.upper()} 알림"
    if is_operator_fallback:
        subject = "[수신처 미설정] " + subject

    fallback_note = (
        "\n    ⚠️ 이 고객은 알림 수신 이메일이 설정돼 있지 않아, 고객 대신 운영자에게 발송된\n"
        "    메일입니다. 설정>알림 수신에 병원 담당자 이메일을 입력해야 고객에게 전달됩니다.\n"
        if is_operator_fallback else ""
    )

    body = f"""
    Keepy 모니터링 알림
{fallback_note}
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
        # local_hostname을 명시적으로 고정한다. 지정하지 않으면 smtplib가 OS 호스트명을
        # EHLO로 보내는데, 호스트명에 비ASCII(예: 한글 PC 이름)가 있으면 인코딩 오류로
        # 발송이 통째로 실패한다.
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, local_hostname="localhost")
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.debug(f"알림 이메일 발송 성공: site_name={site_name} 수신={to_list}")
        return True
    except Exception as e:
        logger.error(f"알림 이메일 발송 실패: {str(e)}")
        return False
