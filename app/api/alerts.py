from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["alerts"])

@router.get("/", response_model=List[schemas.Alert])
def get_alerts(limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Alert)
    if current_user.role != models.UserRole.SUPERADMIN:
        allowed_site_ids = [m.site_id for m in current_user.memberships]
        query = query.filter(models.Alert.site_id.in_(allowed_site_ids))
    return query.order_by(models.Alert.created_at.desc()).limit(limit).all()
