from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["alerts"])

@router.get("/", response_model=List[schemas.Alert])
def list_alerts(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    알림 내역을 조회합니다.
    - Superadmin: 모든 알림 조회 가능
    - User: 자신이 소속된 조직의 사이트 알림만 조회 가능
    """
    query = db.query(models.Alert)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        # 사용자가 속한 조직의 모든 사이트 ID 가져오기
        allowed_site_ids = db.query(models.Site.id).join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        ).all()
        allowed_site_ids = [id[0] for id in allowed_site_ids]
        query = query.filter(models.Alert.site_id.in_(allowed_site_ids))
        
    return query.order_by(models.Alert.created_at.desc()).limit(limit).all()


@router.get("/undelivered", response_model=List[schemas.Alert])
def list_undelivered_alerts(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """발송에 실패한(이메일 미전달) 알림 목록.

    sent_at이 비어 있는 알림 = 재시도까지 실패해 고객에게 닿지 못한 알림.
    운영자가 이걸 보고 직접 병원에 연락하거나 SMTP 문제를 조치한다.
    (제품 핵심 가치인 '알림 전달'이 조용히 사라지지 않게 하는 안전망)
    """
    query = db.query(models.Alert).filter(models.Alert.sent_at.is_(None))

    if current_user.role != models.UserRole.SUPERADMIN:
        allowed_site_ids = db.query(models.Site.id).join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        ).all()
        allowed_site_ids = [id[0] for id in allowed_site_ids]
        query = query.filter(models.Alert.site_id.in_(allowed_site_ids))

    return query.order_by(models.Alert.created_at.desc()).limit(limit).all()
