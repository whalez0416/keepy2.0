from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["logs"])

@router.get("/", response_model=List[schemas.Log])
def list_logs(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Log)
    if current_user.role != models.UserRole.SUPERADMIN:
        allowed_site_ids = [m.site_id for m in current_user.memberships]
        query = query.filter(models.Log.site_id.in_(allowed_site_ids))
    return query.order_by(models.Log.checked_at.desc()).limit(limit).all()

@router.get("/{site_id}", response_model=List[schemas.Log])
def get_site_logs(site_id: int, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.SUPERADMIN:
        membership = db.query(models.Membership).filter(
            models.Membership.user_id == current_user.id,
            models.Membership.site_id == site_id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="접근 권한이 없는 사이트입니다.")
            
    return db.query(models.Log).filter(models.Log.site_id == site_id).order_by(models.Log.checked_at.desc()).limit(limit).all()
