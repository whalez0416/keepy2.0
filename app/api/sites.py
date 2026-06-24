from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from ..services.scheduler_service import update_site_jobs, remove_site_jobs
from ..utils.url_guard import is_public_url
from .auth import get_current_user, require_org_writer

router = APIRouter(tags=["sites"])


def _guard_url(url, label: str):
    """저장될 URL이 공인 주소인지 검증(SSRF 방어). 빈 값은 통과."""
    if url and not is_public_url(url):
        raise HTTPException(
            status_code=400,
            detail=f"{label}: 내부망/사설 주소 또는 잘못된 URL은 등록할 수 없습니다.",
        )

@router.post("/", response_model=schemas.Site)
def create_site(site: schemas.SiteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 조직 결정 로직
    if current_user.role == models.UserRole.SUPERADMIN and site.org_id:
        org_id = site.org_id
    else:
        # 일반 유저는 자신이 속한 조직으로 강제
        membership = db.query(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id).first()
        if not membership:
            raise HTTPException(status_code=403, detail="사용자가 속한 조직이 없습니다.")
        org_id = membership.org_id

    # 쓰기 권한 확인(VIEWER 차단)
    require_org_writer(db, current_user, org_id)

    # SSRF 방어: 서버가 주기적으로 fetch할 모든 URL을 저장 전에 검증
    _guard_url(site.homepage_url, "홈페이지 주소")
    for form in (site.form_configs or []):
        _guard_url(form.form_url, "상담폼 주소")
    for spam in (site.spam_configs or []):
        _guard_url(spam.board_url, "게시판 주소")

    # Site 데이터 추출 (DB 모델에 없는 필드 제외)
    exclude_fields = {"form_configs", "spam_configs", "org_id", "expected_phone", "expected_kakao_url"}
    site_data = site.model_dump(exclude=exclude_fields)
    db_site = models.Site(**site_data, org_id=org_id)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    
    # 연락처 감시 설정 추가 (SiteBase에 포함된 필드 처리)
    if site.expected_phone or site.expected_kakao_url:
        db_contact = models.ContactConfig(
            site_id=db_site.id,
            expected_phone=site.expected_phone,
            expected_kakao_url=site.expected_kakao_url
        )
        db.add(db_contact)
    
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
    
    # 스케줄러 작업 등록/업데이트
    update_site_jobs(db_site)
    return db_site

@router.get("/", response_model=List[schemas.Site])
def list_sites(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role == models.UserRole.SUPERADMIN:
        return db.query(models.Site).all()
    
    # 사용자가 속한 조직들의 모든 사이트 조회
    return db.query(models.Site).join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id).all()

@router.get("/{site_id}", response_model=schemas.Site)
def get_site(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)
        
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")
    return site

@router.patch("/{site_id}", response_model=schemas.Site)
def update_site(site_id: int, site_update: schemas.SiteUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)
        
    db_site = query.first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")

    # 쓰기 권한 확인(VIEWER 차단)
    require_org_writer(db, current_user, db_site.org_id)

    # SSRF 방어: 변경되는 URL을 저장 전에 검증
    _guard_url(site_update.homepage_url, "홈페이지 주소")
    for form in (site_update.form_configs or []):
        _guard_url(form.form_url, "상담폼 주소")
    for spam in (site_update.spam_configs or []):
        _guard_url(spam.board_url, "게시판 주소")

    update_data = site_update.model_dump(exclude_unset=True, exclude={"form_configs", "spam_configs"})
    
    # Superadmin만 조직 변경 가능
    if "org_id" in update_data and current_user.role != models.UserRole.SUPERADMIN:
        del update_data["org_id"]

    for var, value in update_data.items():
        setattr(db_site, var, value)
    
    # 폼 설정 업데이트 (전체 교체 방식)
    if site_update.form_configs is not None:
        # 비밀번호는 응답으로 내려주지 않으므로(쓰기전용), 클라이언트가 빈 값으로 보낼 수 있다.
        # 그 경우 기존 비밀번호를 잃지 않도록 폼 이름 기준으로 보존한다.
        old_form_pw = {f.name: f.password_value for f in db_site.form_configs}
        db.query(models.FormConfig).filter(models.FormConfig.site_id == db_site.id).delete()
        for form in site_update.form_configs:
            data = form.model_dump()
            if not data.get("password_value"):
                data["password_value"] = old_form_pw.get(form.name)  # 빈 값이면 기존 비번 유지
            db_form = models.FormConfig(**data, site_id=db_site.id)
            db.add(db_form)

    # 스팸 설정 업데이트 (전체 교체 방식)
    if site_update.spam_configs is not None:
        old_spam_pw = {s.board_url: s.admin_pw for s in db_site.spam_configs}
        db.query(models.SpamConfig).filter(models.SpamConfig.site_id == db_site.id).delete()
        for spam in site_update.spam_configs:
            data = spam.model_dump(exclude={"site_id"})
            if not data.get("admin_pw"):
                data["admin_pw"] = old_spam_pw.get(spam.board_url)  # 빈 값이면 기존 비번 유지
            db_spam = models.SpamConfig(**data, site_id=db_site.id)
            db.add(db_spam)
        
    db.commit()
    db.refresh(db_site)
    update_site_jobs(db_site)
    return db_site

@router.delete("/{site_id}")
def deactivate_site(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)
        
    db_site = query.first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")

    # 쓰기 권한 확인(VIEWER 차단)
    require_org_writer(db, current_user, db_site.org_id)

    db_site.is_active = False
    db.commit()
    remove_site_jobs(site_id)
    return {"status": "deactivated"}

@router.get("/public/{site_id}/banner")
def get_public_banner_status(site_id: int, db: Session = Depends(get_db)):
    """
    고객사 홈페이지에 심긴 스크립트가 호출하는 공개 엔드포인트
    """
    site = db.query(models.Site).filter(models.Site.id == site_id, models.Site.is_active == True).first()
    if not site:
        return {"active": False}
    
    return {
        "active": site.emergency_mode_active,
        "message": site.emergency_message or "현재 시스템 점검 중입니다. 서비스 이용에 불편을 드려 죄송합니다."
    }
