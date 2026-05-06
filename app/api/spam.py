"""
AI Spam API Endpoint
AI 기반 스팸 탐지 및 분석
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models
from ..services.ai_spam_classifier import run_ai_spam_hunter, classify_posts_ai
from ..utils.logger import get_logger
from .auth import get_current_user

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


@router.get("/configs/{site_id}")
def get_spam_configs(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """특정 사이트의 스팸 설정 목록 조회"""
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


@router.post("/configs")
def create_spam_config(config: SpamConfigCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """스팸 설정 생성"""
    # 사이트 권한 확인
    site_query = db.query(models.Site).filter(models.Site.id == config.site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        site_query = site_query.join(models.Organization).join(models.OrganizationMember).filter(
            models.OrganizationMember.user_id == current_user.id
        )
    
    if not site_query.first():
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
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
    
    if not site_query.first():
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    result = run_ai_spam_hunter(db, config)
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
    
    if not site_query.first():
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    db.delete(config)
    db.commit()
    return {"status": "deleted"}
