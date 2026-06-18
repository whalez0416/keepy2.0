import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["logs"])


def _user_can_access_site(db: Session, current_user: models.User, site_id: int) -> bool:
    if current_user.role == models.UserRole.SUPERADMIN:
        return True
    allowed = db.query(models.Site.id).join(models.Organization).join(models.OrganizationMember).filter(
        models.OrganizationMember.user_id == current_user.id,
        models.Site.id == site_id,
    ).first()
    return allowed is not None


@router.get("/screenshot/{log_id}")
def get_log_screenshot(log_id: int, download: bool = False,
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(get_current_user)):
    """점검 로그의 스크린샷 이미지를 인증된 사용자에게 제공한다.

    download=true 면 첨부파일(다운로드)로, 아니면 인라인으로 반환한다.
    보존기간이 지나 자동 삭제된 경우 404.
    """
    log = db.query(models.Log).filter(models.Log.id == log_id).first()
    if not log or not log.screenshot_path:
        raise HTTPException(status_code=404, detail="스크린샷이 없습니다.")
    if not _user_can_access_site(db, current_user, log.site_id):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    # screenshot_path 예: "screenshots/site_1_form_2_2026....png"
    path = os.path.join("app", "static", log.screenshot_path)
    # 경로 이탈 방지(정상값은 screenshots/ 하위)
    base = os.path.abspath(os.path.join("app", "static", "screenshots"))
    if not os.path.abspath(path).startswith(base) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="스크린샷 파일이 만료되었거나 없습니다.")

    filename = f"keepy_screenshot_site{log.site_id}_log{log.id}.png"
    return FileResponse(
        path,
        media_type="image/png",
        filename=filename if download else None,
    )

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
