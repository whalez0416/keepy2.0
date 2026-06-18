from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models import Site, Log, Alert
from .email_service import send_alert_email
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("alert_service")


def _recipients_for_site(site: Site):
    """사이트가 속한 조직의 알림 수신 이메일 목록을 반환한다.

    우선순위: organization.notify_emails → billing_email → (빈 목록 → 운영자 폴백은
    email_service가 처리). 휴대폰 번호는 SMS/알림톡 연동 시 사용하도록 함께 반환.
    """
    emails, phones = [], []
    org = getattr(site, "organization", None)
    if org:
        if org.notify_emails:
            emails = [e.strip() for e in org.notify_emails.split(",") if e.strip()]
        if not emails and org.billing_email:
            emails = [org.billing_email.strip()]
        if org.notify_phones:
            phones = [p.strip() for p in org.notify_phones.split(",") if p.strip()]
    return emails, phones


def handle_check_result(db: Session, site: Site, check_type: str, status: str, fail_reason: str):
    if status == "success":
        # 성공 시 로직 (필요 시 알림 해제 등 추가 가능)
        return

    # 알림 쿨다운 확인
    recent_alert = db.query(Alert).filter(
        Alert.site_id == site.id,
        Alert.check_type == check_type,
        Alert.created_at >= datetime.utcnow() - timedelta(hours=settings.ALERT_COOLDOWN_HOURS)
    ).first()

    if recent_alert:
        logger.debug(f"알림 억제: site_id={site.id} type={check_type} (쿨다운 시간 미경과)")
        return

    should_alert = False
    alert_level = "warning"

    if check_type.startswith("form") and status == "fail":
        # 스케줄러는 "form:<폼이름>" 형태로 넘기므로 정확 일치가 아닌 접두어로 판별
        should_alert = True
        alert_level = "danger"
    elif check_type == "spam" and status in ("warning", "fail"):
        # AI 스팸 헌터가 스팸을 탐지하면 알림
        should_alert = True
        alert_level = "warning"
    elif check_type == "contact_hijack" and status == "fail":
        # 헤드라인 기능: 전화번호/카카오 링크 변조 — 즉시 긴급 알림
        should_alert = True
        alert_level = "danger"
    elif check_type == "visual_defacement" and status in ("warning", "fail"):
        # 홈페이지 화면 변조 의심
        should_alert = True
        alert_level = "warning"
    elif check_type == "ssl":
        # SSL 만료/오류: fail=긴급, warning=만료 임박
        should_alert = True
        alert_level = "danger" if status == "fail" else "warning"
    elif check_type == "homepage" and status == "fail":
        # 이전 점검 결과도 실패였는지 확인 (2회 연속 실패 시 알림)
        last_logs = db.query(Log).filter(
            Log.site_id == site.id,
            Log.check_type == "homepage"
        ).order_by(desc(Log.checked_at)).limit(2).all()

        if len(last_logs) >= 2 and all(l.status == "fail" for l in last_logs):
            should_alert = True
            alert_level = "warning"

    if should_alert:
        logger.debug(f"알림 발생: site_id={site.id} type={check_type} level={alert_level}")
        
        # 데이터베이스에 알림 기록 저장
        alert = Alert(
            site_id=site.id,
            check_type=check_type,
            alert_level=alert_level,
            message=fail_reason,
            created_at=datetime.utcnow()
        )
        db.add(alert)
        db.commit()

        # 고객 조직의 수신처 계산 (이메일은 즉시 발송, 휴대폰은 SMS/알림톡 연동 시)
        emails, phones = _recipients_for_site(site)
        if phones:
            # SMS/카카오 알림톡 게이트웨이 미연동 — 발송 대신 기록만 (거짓 발송 금지)
            logger.info(f"SMS 알림 대상 {phones} (게이트웨이 미연동 — 발송 보류): site_id={site.id}")

        # 이메일 발송
        success = send_alert_email(
            site_name=site.site_name,
            check_type=check_type,
            status=status,
            fail_reason=fail_reason,
            checked_at=datetime.utcnow().isoformat(),
            recipients=emails,
        )

        if success:
            alert.sent_at = datetime.utcnow()
            db.commit()
            logger.debug(f"알림 발송 완료: site_id={site.id} check_type={check_type}")
