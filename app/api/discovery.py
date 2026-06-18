"""
Auto-Discovery API Endpoint
병원 홈페이지 URL → 상담폼 자동 탐색
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..services.auto_discovery import discover_site
from ..utils.logger import get_logger
from ..utils.url_guard import is_public_url
from .. import models
from .auth import get_current_user

logger = get_logger("api_discovery")

router = APIRouter(tags=["discovery"])


class DiscoveryRequest(BaseModel):
    homepage_url: str


class DiscoveryResponse(BaseModel):
    success: bool
    homepage_url: str
    discovered_forms: list
    error: Optional[str] = None


@router.post("/discover", response_model=DiscoveryResponse)
def run_discovery(request: DiscoveryRequest, current_user: models.User = Depends(get_current_user)):
    """
    병원 홈페이지 URL을 입력하면 상담폼 URL과 셀렉터를 자동으로 탐색합니다.
    
    - 홈페이지에서 상담/예약 관련 링크를 자동 탐색
    - 각 링크 페이지에서 폼 셀렉터 자동 탐지
    - 신뢰도 순으로 결과 반환
    """
    logger.info(f"[API] Auto-discovery 요청: {request.homepage_url}")
    
    if not request.homepage_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="유효한 URL을 입력해주세요 (http:// 또는 https:// 로 시작)")

    # SSRF 방어: 내부망/메타데이터 주소로의 요청 차단
    if not is_public_url(request.homepage_url):
        raise HTTPException(status_code=400, detail="내부망/사설 주소는 점검할 수 없습니다.")

    result = discover_site(request.homepage_url)
    return result
