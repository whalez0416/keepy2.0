from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models import Site, Log, Alert
from .email_service import send_alert_email
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("alert_service")

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

    if check_type == "form" and status == "fail":
        should_alert = True
        alert_level = "danger"
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

        # 이메일 발송
        success = send_alert_email(
            site_name=site.site_name,
            check_type=check_type,
            status=status,
            fail_reason=fail_reason,
            checked_at=datetime.utcnow().isoformat()
        )
        
        if success:
            alert.sent_at = datetime.utcnow()
            db.commit()
            logger.debug(f"알림 발송 완료: site_id={site.id} check_type={check_type}")
