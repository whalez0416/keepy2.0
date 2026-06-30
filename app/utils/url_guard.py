"""사용자 입력 URL의 SSRF 방어.

discovery/scan 처럼 사용자가 임의의 URL을 넣고 서버가 그 주소로 요청을 보내는
엔드포인트에서, 내부망/루프백/클라우드 메타데이터(169.254.169.254) 같은
사설·예약 IP로 향하는 요청을 차단한다.
"""
import ipaddress
import socket
from urllib.parse import urlparse


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # 파싱 불가 → 안전하게 차단
    # 공인(global)만 허용. 사설/루프백/링크로컬/예약/멀티캐스트 등은 차단.
    return not ip.is_global


def is_public_url(url: str) -> bool:
    """URL이 http(s) 스킴이고, 호스트가 공인 IP로만 해석되면 True."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False

    # 호스트명이 해석되는 모든 IP가 공인이어야 함(여러 A/AAAA 레코드 대비)
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False

    if not infos:
        return False

    for info in infos:
        ip_str = info[4][0]
        if _is_blocked_ip(ip_str):
            return False
    return True


def validate_public_url(url: str):
    """공인 URL이 아니면 ValueError를 던진다(엔드포인트에서 400으로 변환)."""
    if not is_public_url(url):
        raise ValueError("내부망/사설 주소 또는 잘못된 URL은 허용되지 않습니다.")


def safe_get(url: str, *, max_redirects: int = 5, **kwargs):
    """SSRF에 안전한 requests.get.

    저장 시점에만 URL을 검증하면, ①공인 URL이 내부주소(169.254.169.254 등)로
    리다이렉트하거나 ②DNS를 나중에 내부 IP로 바꾸는(rebinding) 우회가 가능하다.
    이 함수는 **요청 직전에** 호스트를 다시 해석해 공인 IP인지 확인하고, 리다이렉트를
    자동으로 따르지 않고 각 홉의 Location을 매번 재검증하며 수동으로 따라간다.

    requests를 import하는 쪽 부담을 줄이려 함수 안에서 지연 import한다.
    """
    import requests

    kwargs.pop("allow_redirects", None)  # 항상 수동 처리(자동 추적 금지)
    current = url
    for _ in range(max_redirects + 1):
        if not is_public_url(current):
            raise ValueError(f"내부망/사설 주소로의 요청 차단: {current}")
        resp = requests.get(current, allow_redirects=False, **kwargs)
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            if not location:
                return resp
            current = requests.compat.urljoin(current, location)
            continue
        return resp
    raise ValueError("리다이렉트가 너무 많습니다(우회 시도 가능).")
