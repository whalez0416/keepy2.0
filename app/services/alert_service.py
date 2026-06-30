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

    # 알림 중복 억제: '미해결 상태가 지속되는 동안 1번만' 보낸다.
    # 과거엔 고정 1시간 쿨다운이라, 매일(SSL/화면)·6시간(스팸/관리자) 주기 점검은
    # 쿨다운(1h)을 항상 넘겨 같은 문제로 매 주기 알림이 반복됐다.
    # → 같은 check_type의 가장 최근 알림이 있고, 그 이후로 같은 점검이 '정상(success)'으로
    #   돌아온 적이 없다면(=아직 미해결), 재알림하지 않는다. 정상 복구 후 재발하면 다시 알린다.
    last_alert = db.query(Alert).filter(
        Alert.site_id == site.id,
        Alert.check_type == check_type,
    ).order_by(desc(Alert.created_at)).first()

    if last_alert:
        # 마지막 알림 이후로 이 점검이 정상으로 회복된 로그가 있었는지 확인.
        # (알림 check_type과 로그 check_type은 동일하다: homepage / form:<name> /
        #  contact_hijack / visual_defacement / ssl / admin_exposure)
        recovered = db.query(Log).filter(
            Log.site_id == site.id,
            Log.check_type == check_type,
            Log.status == "success",
            Log.checked_at > last_alert.created_at,
        ).first()
        # 안전장치: 점검 주기가 매우 긴 경우(예: 일간)에도 최소 하루에 한 번은 재고지할 수 있게,
        # 마지막 알림이 24시간 이상 지났으면 회복 여부와 무관하게 재알림 허용.
        stale = last_alert.created_at < datetime.utcnow() - timedelta(hours=24)
        if not recovered and not stale:
            logger.debug(f"알림 억제: site_id={site.id} type={check_type} (미해결 상태 지속 — 중복 알림 생략)")
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
        # 연락처 변조는 오탐 위험이 있다(대표번호가 이미지로 박혀 텍스트엔 팩스/지점번호만
        # 노출되는 병원 사이트 등). 단발성 오탐을 거르기 위해 '2회 연속 fail'일 때만 경보한다.
        recent = db.query(Log).filter(
            Log.site_id == site.id, Log.check_type == "contact_hijack"
        ).order_by(desc(Log.checked_at)).limit(2).all()
        if len(recent) >= 2 and all(l.status == "fail" for l in recent):
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
    elif check_type == "admin_exposure" and status == "warning":
        # 관리자 페이지가 로그인 없이 노출 의심 — 보안 긴급
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
