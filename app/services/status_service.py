from sqlalchemy.orm import Session
from app.models import Site, Log, Alert
from datetime import datetime, timedelta

def get_site_status(db: Session, site: Site):
    """
    사이트의 현재 상태를 계산합니다.
    - 비활성: is_active=False
    - 위험: 최근 24시간 내 'danger' 레벨 알림이 있거나 최근 로그가 'fail'
    - 주의: 최근 24시간 내 'warning' 로그가 있음
    - 정상: 그 외
    """
    if not site.is_active:
        return "비활성", "secondary"

    # 최근 24시간 기준
    since = datetime.now() - timedelta(hours=24)
    
    # 위험 판단: 최근 폼 실패 로그가 있거나 홈페이지 2회 연속 실패 중인지 확인
    # 간단하게 최근 알림 테이블 확인
    recent_alert = db.query(Alert).filter(
        Alert.site_id == site.id,
        Alert.created_at >= since,
        Alert.level == "danger"
    ).first()
    
    if recent_alert:
        return "위험", "danger"
        
    # 주의 판단: 최근 warning 로그가 있는지 확인
    recent_warning = db.query(Log).filter(
        Log.site_id == site.id,
        Log.created_at >= since,
        Log.status == "warning"
    ).first()
    
    if recent_warning:
        return "주의", "warning"
        
    return "정상", "success"

def get_site_summary(db: Session, site: Site):
    status_text, status_color = get_site_status(db, site)
    
    last_log = db.query(Log).filter(Log.site_id == site.id).order_by(Log.created_at.desc()).first()
    last_check_time = last_log.created_at if last_log else None
    
    last_success = db.query(Log).filter(
        Log.site_id == site.id, 
        Log.status == "success"
    ).order_by(Log.created_at.desc()).first()
    last_success_time = last_success.created_at if last_success else None
    
    return {
        "id": site.id,
        "site_name": site.site_name,
        "homepage_url": site.homepage_url,
        "form_url": site.form_url,
        "status_text": status_text,
        "status_color": status_color,
        "last_check_time": last_check_time,
        "last_success_time": last_success_time,
        "last_screenshot": last_success.screenshot_path if last_success else None,
        "is_active": site.is_active
    }
