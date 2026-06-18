import time
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session
from datetime import datetime
from ..models import Site, Log, ContactConfig
from ..utils.logger import get_logger
from .browser_pool import browser_semaphore
import re

logger = get_logger("contact_checker")

def check_contact(db: Session, contact_config: ContactConfig):
    if not contact_config or not contact_config.is_active:
        return None

    site = contact_config.site
    logger.debug(f"연락처 변조 체크 시작: site_id={site.id} url={site.homepage_url}")
    
    start_time = time.time()
    status = "success"
    fail_reasons = []
    
    try:
        with browser_semaphore:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # 1. 홈페이지 이동
                page.goto(site.homepage_url, timeout=30000)
                # networkidle은 채팅위젯·트래커 등으로 영영 안 끝날 수 있어 타임아웃을 명시.
                # 타임아웃돼도 추출은 진행(예외로 변조 오경보가 나지 않게).
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                # 2. 연락처 데이터 추출
                # 병원 사이트는 전화번호를 tel: 링크가 아니라 '평문 텍스트'로 적는 경우가
                # 훨씬 많다. 따라서 tel: 링크뿐 아니라 페이지 본문 텍스트에서도 번호를 찾고,
                # 카카오 링크도 페이지 내 모든 a[href]를 훑어 후보를 모은다.

                # (1) 전화번호 후보 모으기 (tel: 링크 + 본문 텍스트의 전화번호 패턴)
                phone_candidates = set()  # 숫자만 정규화한 값들
                phone_sel = contact_config.phone_selector or 'a[href^="tel:"]'
                try:
                    for el in page.query_selector_all(phone_sel):
                        href = el.get_attribute("href") or el.inner_text()
                        if href:
                            d = re.sub(r'[^0-9]', '', href.replace("tel:", ""))
                            if len(d) >= 8:
                                phone_candidates.add(d)
                except Exception as e:
                    logger.debug(f"전화번호 셀렉터 추출 건너뜀: {e}")

                page_text = ""
                try:
                    page_text = page.inner_text("body")
                except Exception:
                    page_text = page.content()
                for m in re.findall(r'0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}', page_text):
                    d = re.sub(r'[^0-9]', '', m)
                    if len(d) >= 8:
                        phone_candidates.add(d)

                # (2) 카카오 링크 후보 모으기 (페이지 내 모든 a[href] 중 카카오 도메인)
                kakao_candidates = set()
                try:
                    for el in page.query_selector_all('a[href]'):
                        href = (el.get_attribute("href") or "").strip()
                        if href and ("kakao.com" in href or "pf.kakao.com" in href or "open.kakao" in href):
                            kakao_candidates.add(href)
                except Exception as e:
                    logger.debug(f"카카오 링크 추출 건너뜀: {e}")

                # 3. 무결성 검증
                # 핵심 원칙(오경보 방지): 기대값이 페이지 어딘가에 그대로 있으면 '정상'.
                # 기대값은 없는데 '다른' 연락처가 보이면 '변조 의심'(경보).
                # 아무 연락처도 못 찾으면(이미지/JS 렌더 등) 섣불리 긴급경보 하지 않고 판단 보류.
                inconclusive = []

                if contact_config.expected_phone:
                    expected_norm = re.sub(r'[^0-9]', '', contact_config.expected_phone)
                    # 정확 일치 또는 '끝 8자리(국번+번호)' 일치만 인정한다.
                    # (부분 substring 매칭은 변조를 놓치거나(false negative) 무관한 번호를
                    #  통과시킬 수 있어 위험)
                    def _phone_match(c: str) -> bool:
                        if c == expected_norm:
                            return True
                        tail = expected_norm[-8:]
                        return len(tail) == 8 and c.endswith(tail)
                    matched = any(_phone_match(c) for c in phone_candidates)
                    if matched:
                        pass  # 기대 번호 존재 → 정상
                    elif phone_candidates:
                        status = "fail"
                        fail_reasons.append(
                            f"전화번호 변조 의심: 기대 번호({contact_config.expected_phone})가 보이지 않고 "
                            f"다른 번호가 노출됨 (발견: {', '.join(sorted(phone_candidates))})")
                    else:
                        inconclusive.append("전화번호를 페이지에서 찾지 못함(이미지/스크립트 표기 가능) — 확인 필요")

                if contact_config.expected_kakao_url:
                    matched = any(contact_config.expected_kakao_url in k for k in kakao_candidates)
                    if matched:
                        pass  # 기대 카카오 링크 존재 → 정상
                    elif kakao_candidates:
                        status = "fail"
                        fail_reasons.append(
                            f"카카오 링크 변조 의심: 기대 링크가 보이지 않고 다른 카카오 링크가 노출됨 "
                            f"(발견: {', '.join(sorted(kakao_candidates))})")
                    else:
                        inconclusive.append("카카오 상담 링크를 찾지 못함 — 확인 필요")

                # 판단 보류 항목은 경보(fail) 없이 정보성으로만 기록
                if inconclusive and status != "fail":
                    fail_reasons.extend(inconclusive)

                found_phone = ", ".join(sorted(phone_candidates)) if phone_candidates else None
                found_kakao = ", ".join(sorted(kakao_candidates)) if kakao_candidates else None
                browser.close()
            
        response_time = time.time() - start_time
        
    except Exception as e:
        response_time = time.time() - start_time
        # 시스템 오류(네트워크/타임아웃/브라우저)는 '변조'가 아니다. status=fail로 두면
        # 스케줄러→handle_check_result에서 danger '연락처 변조' 긴급경보가 잘못 나가므로
        # warning으로 기록해 변조 경보가 발생하지 않게 한다(오경보 방지).
        status = "warning"
        fail_reasons.append(f"점검 수행 중 오류(변조 아님): {str(e)}")
        logger.error(f"연락처 체크 시스템 오류: site_id={site.id} 사유={str(e)}")

    # 결과 로그 기록
    fail_reason_text = " | ".join(fail_reasons) if fail_reasons else None
    
    log = Log(
        site_id=site.id,
        check_type="contact_hijack",
        status=status,
        response_time=response_time,
        fail_reason=fail_reason_text,
        raw_result=f"Phone: {found_phone}, Kakao: {found_kakao}" if status == "fail" else None
    )
    db.add(log)

    # 변조 발견 로깅. Alert 생성/이메일은 스케줄러가 handle_check_result로 일원화 처리한다
    # (쿨다운·수신처·중복 방지를 한곳에서 관리하기 위함).
    if status == "fail":
        logger.warning(f"ALERT: 연락처 변조 탐지! site_id={site.id} 사유={fail_reason_text}")

    # 마지막 체크 시간 업데이트
    contact_config.last_checked_at = datetime.now()
    db.commit()

    return log
