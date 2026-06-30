import requests
import json
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("slack_service")

SLACK_WEBHOOK_URL = settings.SLACK_WEBHOOK_URL
# 관리자 리드 페이지 링크 (CORS_ORIGINS의 첫 도메인 또는 상대경로)
_origin = settings.CORS_ORIGINS.split(",")[0].strip()
_admin_link = (f"{_origin}/leads" if _origin and _origin != "*" else "/leads")

def _post_to_slack(message_text: str) -> bool:
    """슬랙 웹훅으로 메시지 전송. 웹훅 미설정 시 로그만 남기고 False."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL 미설정 — 슬랙 전송 생략. 내용:")
        logger.info(message_text)
        return False
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps({"text": message_text}),
            headers={'Content-Type': 'application/json'},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"슬랙 전송 실패: {e}")
        return False


def send_alert_delivery_failure(site_name: str, check_type: str, message: str, recipients) -> bool:
    """고객 알림 이메일이 (재시도 후에도) 발송 실패했을 때 운영자에게 슬랙으로 통보.

    제품의 핵심 가치인 '알림 전달'이 조용히 사라지지 않도록 하는 안전망.
    운영자가 보고 직접 병원에 연락하거나 SMTP 문제를 즉시 조치할 수 있다.
    """
    to = ", ".join(recipients) if recipients else "(수신처 없음)"
    text = (
        f"🚨 *[Keepy 알림 발송 실패]* — 고객에게 알림이 전달되지 못했습니다!\n"
        f"🏥 *사이트:* {site_name}\n"
        f"🔎 *점검 유형:* {check_type}\n"
        f"📧 *원래 수신처:* {to}\n"
        f"📝 *내용:* {message}\n\n"
        f"⚠️ SMTP(Gmail 앱비번 만료·발송한도·차단 등)를 즉시 확인하고, 필요하면 "
        f"병원에 직접 연락하세요."
    )
    ok = _post_to_slack(text)
    if ok:
        logger.info(f"알림 발송 실패를 슬랙으로 운영자에게 통보함: {site_name}/{check_type}")
    return ok


def send_new_lead_notification(lead_data: dict):
    """
    새로운 무료 체험 신청(Lead)이 들어왔을 때 슬랙으로 알림을 보냅니다.
    """
    message_text = (
        f"🚨 *[Keepy 신규 무료체험 신청]* 🚨\n"
        f"새로운 문의가 접수되었습니다!\n\n"
        f"🏥 *병원/기관명:* {lead_data.get('hospital_name')}\n"
        f"👤 *담당자:* {lead_data.get('contact_name')}\n"
        f"📞 *연락처:* {lead_data.get('phone_number')}\n"
        f"📧 *이메일:* {lead_data.get('email')}\n"
        f"🌐 *웹사이트:* {lead_data.get('website_url')}\n"
        f"💳 *관심 요금제:* {lead_data.get('plan')}\n"
        f"📝 *문의 내용:* {lead_data.get('inquiry', '없음')}\n\n"
        f"👉 <{_admin_link}|관리자 페이지에서 확인하기>"
    )

    payload = {
        "text": message_text
    }

    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL이 설정되지 않아 슬랙 알림을 보낼 수 없습니다. 아래 내용이 전송될 예정이었습니다:")
        logger.info(message_text)
        return False

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        logger.info("슬랙 알림 전송 성공!")
        return True
    except Exception as e:
        logger.error(f"슬랙 알림 전송 실패: {e}")
        return False
