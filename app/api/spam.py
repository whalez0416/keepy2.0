"""
AI Spam API Endpoint
AI 기반 스팸 탐지 및 분석
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import SpamConfig, Site
from ..services.ai_spam_classifier import run_ai_spam_hunter, classify_posts_ai
from ..utils.logger import get_logger

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
def scan_board(request: SpamScanRequest):
    """
    게시판 URL을 직접 입력하여 스팸을 즉시 스캔합니다 (임시/테스트용).
    """
    logger.info(f"[API SPAM] 즉시 스캔 요청: {request.board_url}")
    
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
def classify_posts(request: SpamClassifyRequest):
    """
    게시물 목록을 직접 넣어서 AI 스팸 분류 결과를 받습니다.
    """
    keywords = [k.strip() for k in (request.keywords or "").split(",") if k.strip()]
    results = classify_posts_ai(request.posts, keywords)
    return {"results": results, "total": len(results)}


@router.get("/configs/{site_id}")
def get_spam_configs(site_id: int, db: Session = Depends(get_db)):
    """특정 사이트의 스팸 설정 목록 조회"""
    configs = db.query(SpamConfig).filter(SpamConfig.site_id == site_id).all()
    return configs


@router.post("/configs")
def create_spam_config(config: SpamConfigCreate, db: Session = Depends(get_db)):
    """스팸 설정 생성"""
    # 사이트 존재 여부 확인
    site = db.query(Site).filter(Site.id == config.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="사이트를 찾을 수 없습니다")
    
    db_config = SpamConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.post("/configs/{config_id}/run")
def run_spam_config(config_id: int, db: Session = Depends(get_db)):
    """특정 스팸 설정으로 즉시 스팸 헌터 실행"""
    config = db.query(SpamConfig).filter(SpamConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="스팸 설정을 찾을 수 없습니다")
    
    result = run_ai_spam_hunter(db, config)
    return result


@router.delete("/configs/{config_id}")
def delete_spam_config(config_id: int, db: Session = Depends(get_db)):
    """스팸 설정 삭제"""
    config = db.query(SpamConfig).filter(SpamConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="스팸 설정을 찾을 수 없습니다")
    
    db.delete(config)
    db.commit()
    return {"status": "deleted"}
