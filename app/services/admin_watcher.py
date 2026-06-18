import re
import requests
import time
from sqlalchemy.orm import Session
from ..models import Site, Log
from ..utils.logger import get_logger

logger = get_logger("admin_watcher")

# 로그인 폼/인증 화면 신호 — 이게 있으면 관리자 페이지는 '자격증명으로 보호됨'(정상).
_LOGIN_SIGNALS = ["비밀번호", "패스워드", "로그인", "관리자 인증", "login", "log in", "sign in"]
# 로그인 없이 관리자 기능이 그대로 보일 때만 보이는 신호 → 진짜 노출.
_ADMIN_CONTENT_SIGNALS = ["로그아웃", "logout", "대시보드", "dashboard", "회원관리", "회원 관리",
                          "게시물관리", "게시판관리", "관리자 메뉴", "환경설정", "admin panel"]


def check_admin_exposure(db: Session, site: Site):
    """
    관리자 페이지가 '인증 없이' 외부에 노출되어 있는지 감시합니다. (상위 플랜 대상)

    중요: 관리자 페이지에 '로그인 화면'이 뜨는 것은 정상이며 취약점이 아니다.
    (관리 페이지는 원래 접근 가능하고 비밀번호로 보호된다.) 따라서 단순히
    200이 떴다고 노출로 보지 않고, **로그인 폼이 없는데 관리자 콘텐츠가 그대로
    보이는 경우에만** 노출로 판정해 오경보를 막는다.
    """
    if not site.admin_path:
        return None

    base_url = site.homepage_url.rstrip('/')
    admin_url = f"{base_url}/{site.admin_path.lstrip('/')}"

    logger.debug(f"관리자 페이지 노출 체크 시작: {admin_url}")

    start_time = time.time()
    status = "success"
    fail_reason = None

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(admin_url, headers=headers, timeout=10, allow_redirects=True)
        html = response.text or ""
        low = html.lower()

        # 로그인 폼 존재 여부: password 입력칸 또는 로그인 관련 문구
        has_password_field = bool(re.search(r'type\s*=\s*["\']?password', low))
        has_login_signal = has_password_field or any(s in low for s in _LOGIN_SIGNALS)
        has_admin_content = any(s in low for s in _ADMIN_CONTENT_SIGNALS)

        if response.status_code in (401, 403):
            # 접근 차단됨 → 잘 보호됨
            status = "success"
        elif response.status_code == 200:
            if has_login_signal:
                # 로그인 화면이 뜸 → 정상(보호됨)
                status = "success"
            elif has_admin_content:
                # 로그인 없이 관리자 콘텐츠가 그대로 노출됨 → 진짜 취약점
                status = "warning"
                fail_reason = (f"🚨 [보안 취약점] 관리자 페이지({site.admin_path})가 로그인 없이 "
                               f"외부에 노출된 것으로 보입니다. 허용 IP 외 접근을 차단하세요.")
            else:
                # 로그인 폼도 관리자 콘텐츠도 아님(홈으로 리다이렉트/소프트404 등) → 판단 보류, 경보 안 함
                status = "success"
        # 그 외 상태코드(404/5xx 등)는 노출 아님 → success 유지

    except Exception as e:
        logger.error(f"관리자 페이지 체크 중 오류: {e}")
        status = "fail"  # 시스템 오류(네트워크 등) — 노출 경보로 오인하지 않음
        fail_reason = str(e)

    if status == "warning":
        logger.warning(f"ALERT: 관리자 페이지 무인증 노출 의심! site_id={site.id}")

    log = Log(
        site_id=site.id,
        check_type="admin_exposure",
        status=status,
        response_time=time.time() - start_time,
        fail_reason=fail_reason,
        raw_result=f"URL: {admin_url}, Status: {status}"
    )
    db.add(log)
    db.commit()

    return log
