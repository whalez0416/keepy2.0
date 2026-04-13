import json
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session
from ..models import Site, SpamConfig, Log
from ..utils.logger import get_logger
import time

logger = get_logger("spam_hunter")

def run_spam_hunter(db: Session, config: SpamConfig):
    if not config.is_active:
        return
    
    logger.info(f"[SPAM HUNTER] Start for site_id={config.site_id}, url={config.board_url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # 1. 게시판 이동
            page.goto(config.board_url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # 2. 관리자 로그인 (필요 시)
            # 기획상 그누보드 등 한국형 게시판의 기본 로그인 경로를 시도하거나 
            # config에 login_url을 추가하는 방식으로 고도화 가능
            if config.admin_id and config.admin_pw:
                logger.debug(f"[SPAM HUNTER] Admin login attempt for {config.admin_id}")
                # TODO: 게시판 종류별 로그인 오토메이션 (그누보드, 워드프레스 등)
                pass

            # 3. 스팸 탐지 로직 (단순 키워드 매칭)
            # 게시물 제목들을 읽어옴
            if config.keywords:
                spam_keywords = [k.strip() for k in config.keywords.split(",") if k.strip()]
                
                # 일반적인 게시판 제목 셀렉터 (그누보드 등 대응)
                # 실제 운영 시에는 사이트별 셀렉터를 config에 저장하는 것이 좋음
                selectors = [".td_subject a", ".list-title", ".tit a", "td.subject a"]
                
                found_spam_count = 0
                for selector in selectors:
                    titles = page.locator(selector).all()
                    if titles:
                        for title_node in titles:
                            title_text = title_node.inner_text()
                            if any(keyword in title_text for keyword in spam_keywords):
                                logger.warning(f"[SPAM HUNTER] Detected spam title: {title_text}")
                                found_spam_count += 1
                                # TODO: 삭제 버튼 클릭 및 확인 로직
                                # page.click(f"text='{title_text}'") -> 삭제 로직 진행
                
                logger.info(f"[SPAM HUNTER] Scan finished. Found {found_spam_count} potential spam posts.")
            
            browser.close()
            
    except Exception as e:
        logger.error(f"[SPAM HUNTER] Error: {e}")
        raise e

def check_all_spam(db: Session):
    configs = db.query(SpamConfig).filter(SpamConfig.is_active == True).all()
    for config in configs:
        try:
            run_spam_hunter(db, config)
        except Exception as e:
            logger.error(f"Failed to run spam hunter for config_id={config.id}: {e}")
