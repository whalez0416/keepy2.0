from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from ..services.scheduler_service import update_site_jobs, remove_site_jobs

router = APIRouter(tags=["sites"])

@router.post("/", response_model=schemas.Site)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db)):
    db_site = models.Site(**site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    # 스케줄러 작업 등록/업데이트
    update_site_jobs(db_site)
    return db_site

@router.get("/", response_model=List[schemas.Site])
def list_sites(db: Session = Depends(get_db)):
    return db.query(models.Site).all()

@router.get("/{site_id}", response_model=schemas.Site)
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.patch("/{site_id}", response_model=schemas.Site)
def update_site(site_id: int, site_update: schemas.SiteUpdate, db: Session = Depends(get_db)):
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    for var, value in site_update.model_dump(exclude_unset=True).items():
        setattr(db_site, var, value)
        
    db.commit()
    db.refresh(db_site)
    # 스케줄러와 동기화
    update_site_jobs(db_site)
    return db_site

@router.delete("/{site_id}")
def deactivate_site(site_id: int, db: Session = Depends(get_db)):
    db_site = db.query(models.Site).filter(models.Site.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    db_site.is_active = False
    db.commit()
    # 스케줄러에서 제거
    remove_site_jobs(site_id)
    return {"status": "deactivated"}
