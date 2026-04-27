"""
Auto-Discovery Service
병원 홈페이지 URL 하나만 입력하면 자동으로:
1. 상담폼/예약폼 URL을 탐색
2. 각 폼의 셀렉터를 자동으로 분석
3. 결과를 JSON으로 반환
"""

import json
import re
import time
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Page, Browser
from urllib.parse import urljoin, urlparse
from ..utils.logger import get_logger

logger = get_logger("auto_discovery")

# 상담폼과 관련된 키워드
FORM_KEYWORDS_KR = [
    "상담", "예약", "문의", "신청", "접수", "상담신청", "예약신청",
    "온라인상담", "온라인예약", "비용상담", "무료상담", "진료예약",
    "consultation", "reservation", "appointment", "inquiry", "contact"
]

# 일반적인 폼 필드 셀렉터 패턴들
FIELD_PATTERNS = {
    "name": [
        "input[name*='name']", "input[name*='nm']", "input[id*='name']",
        "input[placeholder*='이름']", "input[placeholder*='성함']",
        "input[placeholder*='name']", "input[name='writer']",
        "input[name*='user_name']", "input[id*='userName']",
    ],
    "phone": [
        "input[name*='phone']", "input[name*='tel']", "input[name*='mobile']",
        "input[name*='hp']", "input[id*='phone']", "input[id*='tel']",
        "input[placeholder*='전화']", "input[placeholder*='연락처']",
        "input[placeholder*='휴대폰']", "input[placeholder*='phone']",
        "input[type='tel']",
    ],
    "subject": [
        "input[name*='subject']", "input[name*='title']", "input[id*='subject']",
        "input[placeholder*='제목']", "input[placeholder*='subject']",
        "input[name='wr_subject']",
    ],
    "message": [
        "textarea[name*='content']", "textarea[name*='message']",
        "textarea[name*='memo']", "textarea[id*='content']",
        "textarea[placeholder*='내용']", "textarea[placeholder*='상담']",
        "textarea[placeholder*='문의']", "textarea[name='wr_content']",
    ],
    "agreement": [
        "input[type='checkbox'][name*='agree']",
        "input[type='checkbox'][name*='privacy']",
        "input[type='checkbox'][id*='agree']",
        "input[type='checkbox'][id*='privacy']",
        "input[type='checkbox'][name*='personal']",
    ],
    "submit": [
        "button[type='submit']", "input[type='submit']",
        "button:has-text('신청')", "button:has-text('등록')",
        "button:has-text('문의')", "button:has-text('상담')",
        "button:has-text('예약')", "button:has-text('submit')",
        "a:has-text('신청하기')", "a:has-text('문의하기')",
        ".btn_submit", "#btn_submit", "[class*='submit']",
    ]
}

SUCCESS_TEXT_CANDIDATES = [
    "완료", "등록되었습니다", "접수되었습니다", "신청되었습니다",
    "감사합니다", "확인해드리겠습니다", "success", "successfully",
    "제출되었습니다", "완료되었습니다"
]


def _is_same_domain(url: str, base_url: str) -> bool:
    """같은 도메인인지 확인"""
    try:
        base_domain = urlparse(base_url).netloc
        link_domain = urlparse(url).netloc
        return base_domain == link_domain
    except Exception:
        return False


def _find_form_links(page: Page, base_url: str) -> List[Dict[str, str]]:
    """페이지에서 상담/예약 관련 링크를 추출"""
    form_links = []
    
    try:
        # 모든 a 태그 텍스트와 href 가져오기
        links = page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href]').forEach(a => {
                    const text = a.innerText.trim();
                    const href = a.getAttribute('href');
                    if (text && href) {
                        links.push({ text, href });
                    }
                });
                return links;
            }
        """)
        
        for link in links:
            text = link.get("text", "").strip()
            href = link.get("href", "").strip()
            
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            
            # 상담/예약 관련 키워드가 링크 텍스트에 있는지 확인
            is_form_link = any(kw in text for kw in FORM_KEYWORDS_KR)
            is_form_url = any(kw in href.lower() for kw in [
                "consult", "counsel", "reservation", "inquiry", "contact", 
                "apply", "request", "board", "qna", "write", "form",
                "sandam", "yeyak"
            ])
            
            if is_form_link or is_form_url:
                # 절대 URL로 변환
                full_url = urljoin(base_url, href)
                if _is_same_domain(full_url, base_url):
                    form_links.append({
                        "text": text,
                        "url": full_url,
                        "score": (2 if is_form_link else 0) + (1 if is_form_url else 0)
                    })
    except Exception as e:
        logger.error(f"링크 추출 실패: {e}")
    
    # 점수 높은 순 정렬 후 중복 제거
    seen_urls = set()
    unique_links = []
    for link in sorted(form_links, key=lambda x: x["score"], reverse=True):
        if link["url"] not in seen_urls:
            seen_urls.add(link["url"])
            unique_links.append(link)
    
    return unique_links[:10]  # 최대 10개


def _detect_selectors(page: Page) -> Dict[str, Optional[str]]:
    """페이지에서 폼 셀렉터를 자동 탐지"""
    result = {
        "name_selector": None,
        "phone_selector": None,
        "subject_selector": None,
        "message_selector": None,
        "agreement_selector": None,
        "submit_selector": None,
    }
    
    field_map = {
        "name_selector": "name",
        "phone_selector": "phone",
        "subject_selector": "subject",
        "message_selector": "message",
        "agreement_selector": "agreement",
        "submit_selector": "submit",
    }
    
    for result_key, pattern_key in field_map.items():
        patterns = FIELD_PATTERNS.get(pattern_key, [])
        for selector in patterns:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    result[result_key] = selector
                    logger.debug(f"  [{pattern_key}] 셀렉터 발견: {selector}")
                    break
            except Exception:
                continue
    
    return result


def _detect_success_text(page: Page, submit_selector: Optional[str]) -> Optional[str]:
    """폼 제출 후 성공 텍스트 자동 탐지 (dry-run: 실제 제출 없이 추론)"""
    # 현재 페이지에서 가능한 성공 메시지 단서를 찾음
    for text in SUCCESS_TEXT_CANDIDATES:
        try:
            # 숨겨진 메시지 요소나 특정 패턴 확인
            count = page.locator(f"text={text}").count()
            if count > 0:
                return text
        except Exception:
            continue
    
    return "완료"  # 기본값


def _has_form_fields(page: Page) -> bool:
    """페이지에 폼 필드가 있는지 확인"""
    try:
        inputs = page.locator("input:not([type='hidden']):not([type='submit'])").count()
        textareas = page.locator("textarea").count()
        return (inputs + textareas) >= 2
    except Exception:
        return False


def discover_site(homepage_url: str) -> Dict[str, Any]:
    """
    메인 디스커버리 함수
    병원 홈페이지 URL을 받아서 상담폼 정보를 자동으로 탐색
    
    Returns:
        {
            "success": bool,
            "homepage_url": str,
            "discovered_forms": [
                {
                    "url": str,
                    "link_text": str,
                    "selectors": {...},
                    "success_text": str,
                    "confidence": float (0-1)
                }
            ],
            "error": str (if failed)
        }
    """
    logger.info(f"[AUTO-DISCOVERY] 시작: {homepage_url}")
    
    result = {
        "success": False,
        "homepage_url": homepage_url,
        "discovered_forms": [],
        "error": None
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # 1. 홈페이지 접근
            logger.info(f"[AUTO-DISCOVERY] 홈페이지 로드 중...")
            try:
                page.goto(homepage_url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception as e:
                result["error"] = f"홈페이지 접근 실패: {str(e)}"
                browser.close()
                return result
            
            # 2. 팝업/오버레이 닫기 시도
            try:
                page.evaluate("() => { document.querySelectorAll('.btn_close, .close_btn, #close, [title=\"닫기\"], .popup_close').forEach(el => el.click()); }")
                page.wait_for_timeout(500)
            except Exception:
                pass
            
            # 3. 홈페이지 자체가 폼인지 확인
            if _has_form_fields(page):
                logger.info(f"[AUTO-DISCOVERY] 홈페이지 자체에서 폼 필드 발견")
                selectors = _detect_selectors(page)
                if any(v for v in selectors.values()):
                    result["discovered_forms"].append({
                        "url": homepage_url,
                        "link_text": "홈페이지 메인 폼",
                        "selectors": selectors,
                        "success_text": "완료",
                        "confidence": 0.6
                    })
            
            # 4. 상담폼 링크 탐색
            form_links = _find_form_links(page, homepage_url)
            logger.info(f"[AUTO-DISCOVERY] 상담폼 후보 링크 {len(form_links)}개 발견")
            
            # 5. 각 후보 페이지 방문하여 셀렉터 탐지
            checked_count = 0
            for link_info in form_links:
                if checked_count >= 5:  # 최대 5개 페이지만 탐색
                    break
                
                form_url = link_info["url"]
                if form_url == homepage_url:
                    continue
                
                logger.info(f"[AUTO-DISCOVERY] 폼 페이지 탐색: {form_url}")
                
                try:
                    page.goto(form_url, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_timeout(1500)
                    
                    # 팝업 닫기
                    try:
                        page.evaluate("() => { document.querySelectorAll('.btn_close, .close_btn, #close, [title=\"닫기\"]').forEach(el => el.click()); }")
                        page.wait_for_timeout(500)
                    except Exception:
                        pass
                    
                    if not _has_form_fields(page):
                        logger.debug(f"  폼 필드 없음, 건너뜀: {form_url}")
                        checked_count += 1
                        continue
                    
                    selectors = _detect_selectors(page)
                    filled_count = sum(1 for v in selectors.values() if v is not None)
                    
                    if filled_count >= 2:  # 최소 2개 이상의 셀렉터가 탐지되면 유효한 폼으로 판단
                        confidence = min(1.0, filled_count / 5.0)
                        success_text = _detect_success_text(page, selectors.get("submit_selector"))
                        
                        result["discovered_forms"].append({
                            "url": form_url,
                            "link_text": link_info["text"],
                            "selectors": selectors,
                            "success_text": success_text,
                            "confidence": round(confidence, 2),
                            "selector_count": filled_count
                        })
                        logger.info(f"  ✅ 유효한 폼 발견! 셀렉터 {filled_count}개, 신뢰도 {confidence:.0%}")
                    
                    checked_count += 1
                    
                except Exception as e:
                    logger.debug(f"  페이지 탐색 실패: {form_url} → {e}")
                    checked_count += 1
                    continue
            
            browser.close()
        
        # 신뢰도 순으로 정렬
        result["discovered_forms"].sort(key=lambda x: x.get("confidence", 0), reverse=True)
        result["success"] = True
        
        logger.info(f"[AUTO-DISCOVERY] 완료. 유효한 폼 {len(result['discovered_forms'])}개 발견")
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[AUTO-DISCOVERY] 오류 발생: {e}")
    
    return result
