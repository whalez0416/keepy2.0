from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/", response_model=List[schemas.Log])
def get_all_logs(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Log).order_by(models.Log.checked_at.desc()).limit(limit).all()

@router.get("/{site_id}", response_model=List[schemas.Log])
def get_site_logs(site_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(models.Log).filter(models.Log.site_id == site_id).order_by(models.Log.checked_at.desc()).limit(limit).all()
