import os
import requests
import json
from app.utils.logger import get_logger

logger = get_logger("slack_service")

# 슬랙 웹훅 URL (나중에 실제 URL로 교체)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

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
        f"👉 <http://localhost:8000/admin/leads|관리자 페이지에서 확인하기>"
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
