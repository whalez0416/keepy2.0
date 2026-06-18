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
