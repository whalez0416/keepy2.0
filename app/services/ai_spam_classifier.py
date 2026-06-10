"""
AI Spam Classifier Service
OpenAI(GPT) API를 활용한 게시물 스팸 AI 판별 시스템

단순 키워드 매칭을 넘어서 문맥적 스팸 분류를 제공합니다:
- 광고성 게시물
- 악의적 링크 포함
- 의료 허위 정보
- 유사의료 행위 광고
- 일반적 상업 스팸

동작 범위: 탐지 + 알림까지. (게시판 자동 로그인/삭제는 수행하지 않음)
"""

import json
import re
from typing import List, Dict, Optional, Any
from playwright.sync_api import sync_playwright, Page
from sqlalchemy.orm import Session
from ..models import Site, SpamConfig, Log
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("ai_spam_classifier")


# ─────────────────────────────────────────
# OpenAI(GPT) API 기반 스팸 분류 (실제 AI)
# ─────────────────────────────────────────

SPAM_CLASSIFICATION_PROMPT = """당신은 병원 홈페이지 게시판의 스팸 탐지 전문가입니다.
아래 게시물 목록을 분석하여 각 게시물이 스팸인지 판단해주세요.

스팸 판단 기준:
1. 광고/홍보성 내용 (병원과 무관한 상품/서비스 홍보)
2. 불법 의약품 광고, 유사의료 행위 광고
3. 도박, 성인물, 금융사기 관련 내용
4. 의미 없는 반복 문자, 링크 스팸
5. 특수문자 과다 사용, 이상한 URL 포함
6. 외국어 스팸 (의료기관 게시판에 맞지 않는 언어)

정상 게시물 예시:
- "안녕하세요, 다음 주 진료 예약 관련하여 문의드립니다"
- "지난번 치료 후기입니다. 많이 나아졌어요"
- "비용 견적 문의드립니다"
- 테스트성 게시물 (KEEPY_TEST 등)

반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 절대 붙이지 마세요:

{
  "results": [
    {"index": 0, "title": "게시물 제목", "is_spam": true, "confidence": 0.0, "reason": "판단 이유(한국어로 간략히)"}
  ]
}

분석할 게시물:
"""


def _call_openai_api(posts: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
    """OpenAI(GPT) Chat Completions API를 호출하여 스팸 분류."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        logger.warning("[AI SPAM] OPENAI_API_KEY가 설정되지 않았습니다. 키워드 기반으로 폴백합니다.")
        return None

    try:
        import urllib.request

        posts_text = ""
        for i, post in enumerate(posts):
            posts_text += f"{i}. 제목: {post.get('title', '')}\n"
            if post.get('content'):
                posts_text += f"   내용 미리보기: {post.get('content', '')[:200]}\n"

        payload = json.dumps({
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a spam classifier that responds only in the requested JSON format."},
                {"role": "user", "content": SPAM_CLASSIFICATION_PROMPT + posts_text},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        text = data["choices"][0]["message"]["content"]
        text = re.sub(r"```(?:json)?", "", text).strip()
        parsed = json.loads(text)
        return parsed.get("results", [])

    except Exception as e:
        logger.error(f"[AI SPAM] OpenAI API 호출 실패: {e}")
        return None


def _keyword_spam_check(title: str, keywords: List[str]) -> Dict[str, Any]:
    """키워드 기반 스팸 체크 (AI 폴백용)."""
    title_lower = title.lower()

    default_spam_patterns = [
        # 불법 의약품
        "비아그라", "시알리스", "카마그라", "레비트라",
        # 도박
        "카지노", "바카라", "슬롯머신", "토토", "배팅",
        # 성인
        "야동", "성인", "만남", "데이트",
        # 금융사기
        "대출", "급전", "무직자대출", "대환대출",
        # 외국어 스팸
        "click here", "buy now", "limited offer",
    ]

    all_keywords = keywords + default_spam_patterns

    for kw in all_keywords:
        if kw.lower() in title_lower:
            return {
                "is_spam": True,
                "confidence": 0.85,
                "reason": f"스팸 키워드 발견: '{kw}'",
                "method": "keyword",
            }

    return {
        "is_spam": False,
        "confidence": 0.6,
        "reason": "키워드 매칭 없음",
        "method": "keyword",
    }


def _extract_posts_from_page(page: Page, config: SpamConfig) -> List[Dict[str, str]]:
    """게시판 페이지에서 게시물 목록 추출."""
    posts = []

    selectors = [
        ".td_subject a",    # 그누보드
        ".list-title",      # 도넛
        ".tit a",           # 워드프레스
        "td.subject a",     # 일반 테이블형
        ".board-list td a",
        "table.bbs_list td a",
        ".post-title a",
        "h2.entry-title a",
        ".notice_list td a",
        "li.list_item a",
        ".article-list a",
    ]

    for selector in selectors:
        try:
            elements = page.locator(selector).all()
            if elements:
                for el in elements[:30]:
                    try:
                        title = el.inner_text().strip()
                        if title and len(title) > 1:
                            posts.append({"title": title, "content": ""})
                    except Exception:
                        continue
                if posts:
                    logger.debug(f"[AI SPAM] 셀렉터 '{selector}'로 {len(posts)}개 게시물 발견")
                    break
        except Exception:
            continue

    return posts


# ─────────────────────────────────────────
# 메인 스팸 헌터 함수 (탐지 + 알림)
# ─────────────────────────────────────────

def classify_posts_ai(posts: List[Dict[str, str]], keywords: List[str]) -> List[Dict[str, Any]]:
    """게시물 목록을 받아 GPT + 키워드 기반으로 스팸 분류."""
    if not posts:
        return []

    results = []

    # 1. GPT로 전체 분류 시도
    ai_results = _call_openai_api(posts)

    if ai_results:
        logger.info(f"[AI SPAM] GPT 분류 완료: {len(ai_results)}개 게시물")
        for r in ai_results:
            idx = r.get("index", 0)
            r["method"] = "openai_ai"
            r["title"] = posts[idx].get("title", "") if idx < len(posts) else r.get("title", "")
            results.append(r)
        return results

    # 2. AI 실패 시 키워드 기반 폴백
    logger.info(f"[AI SPAM] 키워드 기반 분류 폴백: {len(posts)}개 게시물")
    for i, post in enumerate(posts):
        check = _keyword_spam_check(post["title"], keywords)
        results.append({
            "index": i,
            "title": post["title"],
            "is_spam": check["is_spam"],
            "confidence": check["confidence"],
            "reason": check["reason"],
            "method": check["method"],
        })

    return results


def run_ai_spam_hunter(db: Session, config: SpamConfig) -> Dict[str, Any]:
    """
    AI 스팸 헌터 메인 실행 함수 (탐지 + 결과 반환).
    게시판을 열어 게시물을 추출하고 스팸을 분류한다. (로그인/삭제는 하지 않음)
    """
    if not config.is_active:
        return {"status": "skipped", "reason": "비활성화됨"}

    logger.info(f"[AI SPAM] 시작: site_id={config.site_id}, url={config.board_url}")

    summary = {
        "status": "success",
        "site_id": config.site_id,
        "board_url": config.board_url,
        "total_posts": 0,
        "spam_detected": 0,
        "spam_posts": [],
        "classification_method": "none",
    }

    keywords = [k.strip() for k in (config.keywords or "").split(",") if k.strip()]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()

            page.goto(config.board_url, timeout=30000)
            page.wait_for_load_state("networkidle")

            posts = _extract_posts_from_page(page, config)
            summary["total_posts"] = len(posts)

            if not posts:
                logger.warning(f"[AI SPAM] 게시물을 찾을 수 없음: {config.board_url}")
                summary["status"] = "warning"
                summary["error"] = "게시물을 찾을 수 없습니다. 게시판 구조가 일반적이지 않을 수 있습니다."
                browser.close()
                return summary

            logger.info(f"[AI SPAM] {len(posts)}개 게시물 분석 중...")

            classifications = classify_posts_ai(posts, keywords)

            spam_posts = [c for c in classifications if c.get("is_spam") and c.get("confidence", 0) >= 0.7]
            summary["spam_detected"] = len(spam_posts)
            summary["spam_posts"] = spam_posts

            if classifications:
                summary["classification_method"] = classifications[0].get("method", "unknown")

            logger.info(f"[AI SPAM] 완료: 총 {len(posts)}개 중 스팸 {len(spam_posts)}개 탐지")

            browser.close()

    except Exception as e:
        summary["status"] = "fail"
        summary["error"] = str(e)
        logger.error(f"[AI SPAM] 오류: {e}")

    return summary


def check_all_spam_ai(db: Session) -> List[Dict[str, Any]]:
    """모든 활성 스팸 설정에 대해 AI 스팸 헌터 실행."""
    configs = db.query(SpamConfig).filter(SpamConfig.is_active == True).all()
    results = []
    for config in configs:
        try:
            result = run_ai_spam_hunter(db, config)
            results.append(result)
        except Exception as e:
            logger.error(f"[AI SPAM] site_id={config.site_id} 실패: {e}")
    return results
