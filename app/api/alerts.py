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
