from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["logs"])

@router.get("/", response_model=List[schemas.Log])
def list_logs(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    모니터링 로그 목록을 조회합니다.
    - Superadmin: 모든 로그 조회 가능
    - User: 자신이 속한 조직의 사이트 로그만 조회 가능
    """
    query = db.query(models.Log)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        # 사용자가 속한 조직의 모든 사이트 ID 가져오기
        allowed_site_ids = db.query(models.Site.id).join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        ).all()
        allowed_site_ids = [id[0] for id in allowed_site_ids]
        query = query.filter(models.Log.site_id.in_(allowed_site_ids))
        
    return query.order_by(models.Log.checked_at.desc()).limit(limit).all()

@router.get("/site/{site_id}", response_model=List[schemas.Log])
def get_site_logs(site_id: int, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    특정 사이트의 모니터링 로그를 조회합니다.
    """
    # 사이트 권한 확인
    site_query = db.query(models.Site).filter(models.Site.id == site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        site_query = site_query.join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        )
    
    site = site_query.first()
    if not site:
        raise HTTPException(status_code=403, detail="접근 권한이 없는 사이트이거나 존재하지 않습니다.")
            
    return db.query(models.Log).filter(models.Log.site_id == site_id).order_by(models.Log.checked_at.desc()).limit(limit).all()
