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
from .browser_pool import browser_semaphore
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("ai_spam_classifier")


# ─────────────────────────────────────────
# OpenAI(GPT) API 기반 스팸 분류 (실제 AI)
# ─────────────────────────────────────────

SPAM_CLASSIFICATION_PROMPT = """당신은 병원 홈페이지 '환자 상담/문의 게시판'의 스팸 탐지 전문가입니다.
이 게시판의 글은 대부분 실제 환자/보호자가 남긴 정상 문의입니다. 기본값은 '정상'이며,
명백한 상업/불법 광고일 때만 스팸으로 판정하세요. 애매하면 반드시 정상으로 처리합니다.

스팸으로 판정 (is_spam=true):
1. 병원과 무관한 상품/서비스 광고·홍보 (대출, 코인, 쇼핑몰, 마케팅 대행 등)
2. 불법 의약품(비아그라 등)·유사의료 행위 광고
3. 도박/카지노/토토, 성인물, 금융사기
4. 외부 사이트로 유도하는 도배성 링크, 광고 URL
5. 게시판에 맞지 않는 외국어 광고성 도배

정상으로 판정 (is_spam=false) — 아래는 스팸이 아닙니다:
- 증상/진료/검사/비용/예약(변경·취소) 문의: "목아픔", "발가락 통증", "건강검진 예약변경", "조직검사 문의"
- 오타·띄어쓰기 오류·짧은 제목·반말·비문 (예: "검강검진 에약변경"은 '건강검진 예약변경'의 오타일 뿐 정상)
- 치료 후기, 감사 인사, 테스트성 글(KEEPY_TEST 등)
- 본문이 비어있는 비밀글: 제목만으로 광고가 명백하지 않으면 정상으로 처리

중요: 제목이 짧거나 오타가 있거나 어색하다는 이유만으로 스팸으로 판정하지 마세요.
스팸 여부는 '상업/불법 광고성 의도'가 있는지로만 판단합니다.

confidence는 '해당 글이 스팸일 확률'을 뜻하는 0.0~1.0 사이 숫자입니다.
- is_spam이 true이면 confidence는 반드시 0.7 이상 (광고가 명백하면 0.9~1.0)
- is_spam이 false이면 confidence는 반드시 0.3 이하 (정상이 확실하면 0.0~0.1)
즉 is_spam과 confidence는 항상 같은 방향이어야 합니다. (스팸일수록 1.0에 가깝게)

반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 절대 붙이지 마세요:

{
  "results": [
    {"index": 0, "title": "정상 게시물 제목", "is_spam": false, "confidence": 0.05, "reason": "증상 문의로 정상"},
    {"index": 1, "title": "광고성 게시물 제목", "is_spam": true, "confidence": 0.95, "reason": "대출 광고로 상업적 의도가 명백함"}
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
                posts_text += f"   내용 미리보기: {post.get('content', '')[:300]}\n"

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


# 게시판 목록에서 글 제목/링크를 찾을 때 시도할 셀렉터 (게시판 종류별)
LIST_SELECTORS = [
    ".td_subject a",    # 그누보드
    ".list-title",      # 도넛
    ".tit a",           # 워드프레스
    "td.subject a",     # 일반 테이블형
    "td.noticetitle a", # 킴스큐류(index.php/board) 계열
    ".board-list td a",
    "table.bbs_list td a",
    ".post-title a",
    "h2.entry-title a",
    ".notice_list td a",
    "li.list_item a",
    ".article-list a",
]

# 위 셀렉터가 모두 실패했을 때, 링크 주소(href)에 흔히 나타나는 '글 보기' 패턴으로
# 글을 찾아내는 폴백. (게시판 구조가 특이해도 글 상세 링크는 대개 이런 패턴을 가진다)
POST_HREF_PATTERNS = [
    "/board/view/", "/view/", "/read/",
    "view.php", "read.php", "view.asp", "read.asp",
    "passwordform",          # 비밀글 (제목만 수집, 본문은 비번 필요)
    "wr_id=", "bo_table=",   # 그누보드 쿼리스트링형
    "mode=view", "mode=read",
    "?idx=", "&idx=", "no=", "&id=",
]


def _extract_posts_by_href(page: Page) -> List[tuple]:
    """이름 셀렉터가 실패했을 때, href 패턴으로 (제목, href) 후보를 추출한다."""
    raw = []
    seen = set()
    try:
        anchors = page.eval_on_selector_all(
            "a",
            "els => els.map(e => ({t: (e.innerText||'').trim(), h: e.getAttribute('href') || ''}))",
        )
    except Exception:
        return raw

    for a in anchors:
        title = (a.get("t") or "").strip()
        href = a.get("h") or ""
        if not title or len(title) <= 1:
            continue
        low = href.lower()
        if not any(pat in low for pat in POST_HREF_PATTERNS):
            continue
        key = (title, href)
        if key in seen:
            continue
        seen.add(key)
        raw.append((title, href))
        if len(raw) >= MAX_POSTS:
            break
    return raw

# 게시물 상세 페이지에서 본문을 찾을 때 시도할 셀렉터
POST_CONTENT_SELECTORS = [
    ".contents",            # 킴스큐류(index.php/board) 본문
    ".re_contents",         # 〃 답변 본문
    "#bo_v_con",            # 그누보드5
    ".bo_v_con",
    ".view_content",
    ".board-view-content",
    ".view-content",
    ".read_content",
    ".bbs_content",
    ".entry-content",       # 워드프레스
    "article .content",
    ".post-content",
    ".article-content",
    "#content",
]

# 본문까지 읽는 것은 게시물마다 상세 페이지를 방문하므로, 한 번에 처리할 게시물 수를 제한한다.
MAX_POSTS = 25


def _extract_post_content(page: Page, url: str) -> str:
    """게시물 상세 페이지를 열어 본문 텍스트 미리보기를 추출한다. 실패 시 빈 문자열."""
    try:
        page.goto(url, timeout=20000)
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        return ""

    for selector in POST_CONTENT_SELECTORS:
        try:
            el = page.locator(selector).first
            if el.count() > 0:
                text = el.inner_text().strip()
                if text and len(text) > 10:
                    return text[:500]
        except Exception:
            continue

    # 본문 셀렉터를 못 찾으면 페이지 body 전체 텍스트로 폴백
    try:
        body_text = page.locator("body").inner_text().strip()
        return body_text[:500] if body_text else ""
    except Exception:
        return ""


def _extract_posts_from_page(page: Page, config: SpamConfig) -> List[Dict[str, str]]:
    """게시판 목록에서 (제목, 링크)를 추출하고, 각 게시물 상세 페이지를 방문해 본문 미리보기까지 가져온다."""
    from urllib.parse import urljoin

    list_url = page.url
    raw_posts = []  # (title, href) 쌍

    for selector in LIST_SELECTORS:
        try:
            elements = page.locator(selector).all()
            if elements:
                for el in elements[:MAX_POSTS]:
                    try:
                        title = el.inner_text().strip()
                        href = el.get_attribute("href")
                        if title and len(title) > 1:
                            raw_posts.append((title, href))
                    except Exception:
                        continue
                if raw_posts:
                    logger.debug(f"[AI SPAM] 셀렉터 '{selector}'로 {len(raw_posts)}개 게시물 발견")
                    break
        except Exception:
            continue

    # 이름 셀렉터가 모두 실패하면 href 패턴 폴백으로 글을 찾는다.
    if not raw_posts:
        raw_posts = _extract_posts_by_href(page)
        if raw_posts:
            logger.info(f"[AI SPAM] href 패턴 폴백으로 {len(raw_posts)}개 게시물 발견")

    # 중복 제거 (게시판이 목록을 두 번 렌더링하는 경우 대비) 후 처리 개수 제한
    deduped = []
    seen = set()
    for title, href in raw_posts:
        key = (title, href)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((title, href))
    raw_posts = deduped[:MAX_POSTS]

    # 각 게시물의 본문 미리보기 추출 (상세 페이지 방문)
    posts = []
    for title, href in raw_posts:
        content = ""
        if href and not href.lower().startswith("javascript:"):
            detail_url = urljoin(list_url, href)
            content = _extract_post_content(page, detail_url)
        posts.append({"title": title, "content": content})

    fetched = sum(1 for p in posts if p["content"])
    logger.info(f"[AI SPAM] 게시물 {len(posts)}개 중 {fetched}개 본문 추출 완료")

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
            # is_spam(불리언)과 confidence 방향이 어긋나면 불리언을 신뢰해 보정한다.
            # (GPT가 confidence 의미를 가끔 뒤집어 답해 스팸을 놓치는 것을 방지)
            is_spam = bool(r.get("is_spam"))
            try:
                conf = float(r.get("confidence", 0) or 0)
            except (TypeError, ValueError):
                conf = 0.0
            if is_spam and conf < 0.7:
                conf = 0.8
            elif not is_spam and conf > 0.3:
                conf = 0.1
            r["confidence"] = conf
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
        # 다른 Playwright 점검과 동시에 여러 Chromium이 뜨지 않도록 세마포어로 직렬화하고,
        # 예외가 나도 브라우저가 새지 않도록 try/finally로 반드시 닫는다(메모리 누수 방지).
        with browser_semaphore:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
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
                        return summary

                    logger.info(f"[AI SPAM] {len(posts)}개 게시물 분석 중...")

                    classifications = classify_posts_ai(posts, keywords)

                    spam_posts = [c for c in classifications if c.get("is_spam") and c.get("confidence", 0) >= 0.7]
                    summary["spam_detected"] = len(spam_posts)
                    summary["spam_posts"] = spam_posts

                    if classifications:
                        summary["classification_method"] = classifications[0].get("method", "unknown")

                    logger.info(f"[AI SPAM] 완료: 총 {len(posts)}개 중 스팸 {len(spam_posts)}개 탐지")
                finally:
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
