"""
AI Spam API Endpoint
AI 기반 스팸 탐지 및 분석
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.ai_spam_classifier import run_ai_spam_hunter, classify_posts_ai
from ..services.alert_service import handle_check_result
from ..utils.logger import get_logger
from ..utils.url_guard import is_public_url
from .auth import get_current_user, require_org_writer

logger = get_logger("api_spam")

router = APIRouter(tags=["spam"])


class SpamScanRequest(BaseModel):
    board_url: str
    keywords: Optional[str] = None
    admin_id: Optional[str] = None
    admin_pw: Optional[str] = None


class SpamClassifyRequest(BaseModel):
    posts: List[Dict[str, str]]
    keywords: Optional[str] = None


class SpamConfigCreate(BaseModel):
    site_id: int
    board_url: str
    admin_id: Optional[str] = None
    admin_pw: Optional[str] = None
    keywords: Optional[str] = None
    is_active: bool = True


@router.post("/scan")
def scan_board(request: SpamScanRequest, current_user: models.User = Depends(get_current_user)):
    """
    게시판 URL을 직접 입력하여 스팸을 즉시 스캔합니다 (임시/테스트용).
    """
    logger.info(f"[API SPAM] 즉시 스캔 요청: {request.board_url} (by {current_user.email})")

    # SSRF 방어: 내부망/메타데이터 주소로의 요청 차단
    if not is_public_url(request.board_url):
        raise HTTPException(status_code=400, detail="내부망/사설 주소는 스캔할 수 없습니다.")

    # 임시 config 객체 생성
    class TempConfig:
        site_id = 0
        board_url = request.board_url
        admin_id = request.admin_id
        admin_pw = request.admin_pw
        keywords = request.keywords or ""
        is_active = True
    
    from ..services.ai_spam_classifier import run_ai_spam_hunter
    result = run_ai_spam_hunter(None, TempConfig())
    return result


@router.post("/classify")
def classify_posts(request: SpamClassifyRequest, current_user: models.User = Depends(get_current_user)):
    """
    게시물 목록을 직접 넣어서 AI 스팸 분류 결과를 받습니다.
    """
    keywords = [k.strip() for k in (request.keywords or "").split(",") if k.strip()]
    results = classify_posts_ai(request.posts, keywords)
    return {"results": results, "total": len(results)}


@router.get("/configs/{site_id}", response_model=List[schemas.SpamConfig])
def get_spam_configs(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """특정 사이트의 스팸 설정 목록 조회 (보안: admin_pw는 응답에서 제외됨)"""
    # 권한 확인
    site_query = db.query(models.Site).filter(models.Site.id == site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        site_query = site_query.join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        )
    
    if not site_query.first():
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    configs = db.query(models.SpamConfig).filter(models.SpamConfig.site_id == site_id).all()
    return configs


@router.post("/configs", response_model=schemas.SpamConfig)
def create_spam_config(config: SpamConfigCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """스팸 설정 생성 (보안: admin_pw는 응답에서 제외됨)"""
    # 사이트 권한 확인
    site_query = db.query(models.Site).filter(models.Site.id == config.site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        site_query = site_query.join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        )
    
    site = site_query.first()
    if not site:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    require_org_writer(db, current_user, site.org_id)

    # SSRF 방어: 서버가 주기적으로 fetch할 게시판 URL 검증
    if not is_public_url(config.board_url):
        raise HTTPException(status_code=400, detail="게시판 주소: 내부망/사설 주소는 등록할 수 없습니다.")

    db_config = models.SpamConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.post("/configs/{config_id}/run")
def run_spam_config(config_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """특정 스팸 설정으로 즉시 스팸 헌터 실행"""
    config = db.query(models.SpamConfig).filter(models.SpamConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="스팸 설정을 찾을 수 없습니다")
    
    # 사이트 권한 확인
    site_query = db.query(models.Site).filter(models.Site.id == config.site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        site_query = site_query.join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        )
    
    site = site_query.first()
    if not site:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    require_org_writer(db, current_user, site.org_id)

    result = run_ai_spam_hunter(db, config)
    # 스팸이 탐지되면 즉시 알림(스케줄러와 동일 경로). 쿨다운으로 중복은 자동 억제됨.
    if result and result.get("spam_detected", 0) > 0:
        titles = ", ".join(
            p.get("title", "")[:30] for p in result.get("spam_posts", [])[:5]
        )
        msg = (
            f"🚫 [스팸 탐지] {site.site_name} 게시판에서 의심 게시물 "
            f"{result['spam_detected']}건이 발견되었습니다. (예: {titles})"
        )
        handle_check_result(db, site, "spam", "warning", msg)
    return result


@router.delete("/configs/{config_id}")
def delete_spam_config(config_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """스팸 설정 삭제"""
    config = db.query(models.SpamConfig).filter(models.SpamConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="스팸 설정을 찾을 수 없습니다")
    
    # 사이트 권한 확인
    site_query = db.query(models.Site).filter(models.Site.id == config.site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        site_query = site_query.join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        )
    
    site = site_query.first()
    if not site:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    require_org_writer(db, current_user, site.org_id)

    db.delete(config)
    db.commit()
    return {"status": "deleted"}
