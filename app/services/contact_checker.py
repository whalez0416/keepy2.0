import time
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session
from datetime import datetime
from ..models import Site, Log, ContactConfig, Alert
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
                page.wait_for_load_state("networkidle")
                
                # 2. 연락처 데이터 추출
                
                # (1) 전화번호 체크
                found_phone = None
                phone_sel = contact_config.phone_selector or 'a[href^="tel:"]'
                try:
                    phone_element = page.query_selector(phone_sel)
                    if phone_element:
                        href = phone_element.get_attribute("href")
                        # 'tel:02-123-4567' -> '02-123-4567'
                        found_phone = href.replace("tel:", "").strip()
                except Exception as e:
                    logger.error(f"전화번호 추출 실패: {e}")

                # (2) 카카오톡 링크 체크
                found_kakao = None
                kakao_sel = contact_config.kakao_selector or 'a[href*="kakao.com"], a[href*="pf.kakao.com"]'
                try:
                    kakao_element = page.query_selector(kakao_sel)
                    if kakao_element:
                        found_kakao = kakao_element.get_attribute("href").strip()
                except Exception as e:
                    logger.error(f"카카오 링크 추출 실패: {e}")

                # 3. 무결성 검증 (정규화 후 비교)
                
                # 전화번호 비교 (숫자만 남겨서 비교)
                if contact_config.expected_phone:
                    expected_norm = re.sub(r'[^0-9]', '', contact_config.expected_phone)
                    found_norm = re.sub(r'[^0-9]', '', found_phone) if found_phone else ""
                    
                    if not found_phone:
                        status = "fail"
                        fail_reasons.append("전화번호 링크를 찾을 수 없습니다.")
                    elif expected_norm != found_norm:
                        status = "fail"
                        fail_reasons.append(f"전화번호가 변조되었습니다 (기대: {contact_config.expected_phone}, 발견: {found_phone})")

                # 카카오 링크 비교
                if contact_config.expected_kakao_url:
                    if not found_kakao:
                        status = "fail"
                        fail_reasons.append("카카오톡 상담 링크를 찾을 수 없습니다.")
                    elif contact_config.expected_kakao_url not in found_kakao:
                        status = "fail"
                        fail_reasons.append(f"카카오톡 링크가 변조되었습니다 (기대: {contact_config.expected_kakao_url}, 발견: {found_kakao})")

                browser.close()
            
        response_time = time.time() - start_time
        
    except Exception as e:
        response_time = time.time() - start_time
        status = "fail"
        fail_reasons.append(str(e))
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
    
    # 변조 발견 시 Alert 생성
    if status == "fail":
        alert = Alert(
            site_id=site.id,
            check_type="contact_hijack",
            alert_level="danger",
            message=f"[긴급] 연락처 변조가 의심됩니다: {fail_reason_text}"
        )
        db.add(alert)
        logger.warning(f"ALERT: 연락처 변조 탐지! site_id={site.id} 사유={fail_reason_text}")

    # 마지막 체크 시간 업데이트
    contact_config.last_checked_at = datetime.now()
    db.commit()
    
    return log
