from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from ..services.scheduler_service import update_site_jobs, remove_site_jobs
from .auth import get_current_user

router = APIRouter(tags=["sites"])

@router.post("/", response_model=schemas.Site)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Site 데이터 추출 (form_configs, spam_configs 제외)
    site_data = site.model_dump(exclude={"form_configs", "spam_configs"})
    db_site = models.Site(**site_data)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    
    # 폼 설정들 추가
    if site.form_configs:
        for form in site.form_configs:
            db_form = models.FormConfig(**form.model_dump(), site_id=db_site.id)
            db.add(db_form)
    
    # 스팸 감시 설정들 추가
    if site.spam_configs:
        for spam in site.spam_configs:
            db_spam = models.SpamConfig(**spam.model_dump(exclude={"site_id"}), site_id=db_site.id)
            db.add(db_spam)
            
    db.commit()
    db.refresh(db_site)
    
    # 생성자를 자동으로 OWNER 권한의 멤버로 등록
    membership = models.Membership(
        user_id=current_user.id,
        site_id=db_site.id,
        role=models.MembershipRole.OWNER
    )
    db.add(membership)
    db.commit()
    
    # 스케줄러 작업 등록/업데이트
    update_site_jobs(db_site)
    return db_site

@router.get("/", response_model=List[schemas.Site])
def list_sites(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == models.UserRole.SUPERADMIN:
        return db.query(models.Site).all()
    
    # 사용자가 속한 사이트만 필터링
    return db.query(models.Site).join(models.Membership).filter(models.Membership.user_id == current_user.id).all()

@router.get("/{site_id}", response_model=schemas.Site)
def get_site(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Membership).filter(models.Membership.user_id == current_user.id)
        
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")
    return site

@router.patch("/{site_id}", response_model=schemas.Site)
def update_site(site_id: int, site_update: schemas.SiteUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        # 권한 확인: ADMIN 이상만 수정 가능하게 할 수도 있음 (일단은 멤버면 가능하게)
        query = query.join(models.Membership).filter(models.Membership.user_id == current_user.id)
        
    db_site = query.first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")
        
    for var, value in site_update.model_dump(exclude_unset=True, exclude={"form_configs", "spam_configs"}).items():
        setattr(db_site, var, value)
    
    # 폼 설정 업데이트 (기존 것 삭제 후 재구성)
    if site_update.form_configs is not None:
        db.query(models.FormConfig).filter(models.FormConfig.site_id == db_site.id).delete()
        for form in site_update.form_configs:
            db_form = models.FormConfig(**form.model_dump(), site_id=db_site.id)
            db.add(db_form)

    # 스팸 설정 업데이트 (기존 것 삭제 후 재구성)
    if site_update.spam_configs is not None:
        db.query(models.SpamConfig).filter(models.SpamConfig.site_id == db_site.id).delete()
        for spam in site_update.spam_configs:
            db_spam = models.SpamConfig(**spam.model_dump(exclude={"site_id"}), site_id=db_site.id)
            db.add(db_spam)
        
    db.commit()
    db.refresh(db_site)
    # 스케줄러와 동기화
    update_site_jobs(db_site)
    return db_site

@router.delete("/{site_id}")
def deactivate_site(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Membership).filter(models.Membership.user_id == current_user.id)
        
    db_site = query.first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")
    
    db_site.is_active = False
    db.commit()
    # 스케줄러에서 제거
    remove_site_jobs(site_id)
    return {"status": "deactivated"}
