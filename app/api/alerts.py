from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas

router = APIRouter(tags=["alerts"])

@router.get("/", response_model=List[schemas.Alert])
def get_alerts(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Alert).order_by(models.Alert.created_at.desc()).limit(limit).all()
