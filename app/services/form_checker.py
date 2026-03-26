from playwright.sync_api import sync_playwright
import time
from sqlalchemy.orm import Session
from ..models import Site, Log
from ..utils.logger import get_logger

logger = get_logger("form_checker")

def check_form(db: Session, site: Site):
    if not site.form_url:
        logger.debug(f"상담폼 체크 건너뜀: site_id={site.id} (form_url 없음)")
        return None

    logger.debug(f"상담폼 체크 시작: site_id={site.id} url={site.form_url}")
    
    start_time = time.time()
    status = "fail"
    fail_reason = None
    
    try:
        with sync_playwright() as p:
            # 브라우저 실행 (기본값 헤드리스)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # 1. 상담 페이지 이동
            page.goto(site.form_url, timeout=30000)
            
            # 2. 테스트 데이터 입력
            if site.name_selector:
                page.fill(site.name_selector, "KEEPY_TEST")
            if site.phone_selector:
                page.fill(site.phone_selector, "01000000000")
            if site.message_selector:
                page.fill(site.message_selector, "[KEEPY_TEST] 자동 점검 메시지입니다")
            
            # 3. 제출 버튼 클릭
            if site.submit_selector:
                page.click(site.submit_selector)
            else:
                # 셀렉터가 없는 경우 엔터 키로 제출 시도
                page.keyboard.press("Enter")
                
            # 페이지 전환 및 응답 대기
            page.wait_for_timeout(3000)
            
            # 4. 성공 여부 판단
            content = page.content()
            
            if site.expected_success_text and site.expected_success_text in content:
                status = "success"
            elif "완료" in content or "성공" in content or "제출" in content or "success" in content.lower():
                status = "success"
            else:
                status = "fail"
                fail_reason = "화면 내에서 성공 메시지를 찾을 수 없습니다"
                
            browser.close()
            
        response_time = time.time() - start_time
        logger.debug(f"상담폼 체크 {status}: site_id={site.id} response_time={response_time:.2f}")
        
    except Exception as e:
        response_time = time.time() - start_time
        status = "fail"
        fail_reason = str(e)
        logger.debug(f"상담폼 체크 실패: site_id={site.id} 사유={fail_reason}")

    log = Log(
        site_id=site.id,
        check_type="form",
        status=status,
        response_time=response_time,
        fail_reason=fail_reason,
        raw_result=None
    )
    db.add(log)
    db.commit()
    return log
