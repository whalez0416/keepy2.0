import json
from playwright.sync_api import sync_playwright
import time
from sqlalchemy.orm import Session
from .homepage_checker import check_homepage
import os
from datetime import datetime
from ..models import Site, Log
from ..utils.logger import get_logger

logger = get_logger("form_checker")

def execute_extra_steps(page, steps_json: str):
    if not steps_json:
        return
    
    try:
        steps = json.loads(steps_json)
        for step in steps:
            action_type = step.get("type")
            selector = step.get("selector")
            value = step.get("value")
            
            logger.debug(f"[ADVANCED] Action: {action_type}, Selector: {selector}, Value: {value}")
            
            if action_type == "click":
                page.click(selector, timeout=10000)
            elif action_type == "fill":
                page.fill(selector, value, timeout=10000)
            elif action_type == "select":
                if value and value.startswith("index:"):
                    idx = int(value.split(":")[1])
                    page.select_option(selector, index=idx, timeout=10000)
                else:
                    page.select_option(selector, value=value, timeout=10000)
            elif action_type == "wait":
                wait_time = int(step.get("seconds", 1)) * 1000
                page.wait_for_timeout(wait_time)
            elif action_type == "press":
                page.press(selector, value)
            
            # 각 단계 후 짧은 대기 (안정성 확보)
            page.wait_for_timeout(500)
    except Exception as e:
        logger.error(f"[ADVANCED] 단계 실행 중 오류 발생: {e}")
        raise e

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
            page.wait_for_load_state("networkidle")
            
            # 1.5. 팝업 제거 (사이트 공통 닫기 함수 호출 및 일반 팝업 닫기 시도)
            try:
                page.evaluate("() => { if(typeof layer_close_all2 === 'function') layer_close_all2(); }")
                page.evaluate("() => { document.querySelectorAll('.btn_close, .close_btn, #close, [title=\"닫기\"]').forEach(el => el.click()); }")
                page.wait_for_timeout(1000)
            except:
                pass

            # 1.6. 고급 액션 시퀀스 실행 (복잡한 폼 대응)
            if site.extra_steps_json:
                logger.debug(f"[ADVANCED] 사이트 {site.id}의 고급 액션 시퀀스를 시작합니다.")
                execute_extra_steps(page, site.extra_steps_json)

            # 2. 테스트 데이터 입력
            if site.name_selector:
                page.fill(site.name_selector, "KEEPY_TEST")
            
            if site.phone_selector:
                # 숫자만 입력하도록 처리
                page.fill(site.phone_selector, "01000000000")
            
            if site.subject_selector:
                page.fill(site.subject_selector, "[KEEPY_TEST] 자동 점검 상담 제목입니다")
            
            if site.password_selector:
                pass_val = site.password_value or "keepy1234!"
                page.fill(site.password_selector, pass_val)

            if site.agreement_selector:
                try:
                    page.click(site.agreement_selector)
                except:
                    # 클릭 실패 시 force 클릭 시도
                    page.click(site.agreement_selector, force=True)

            if site.message_selector:
                # Naver SmartEditor (iframe) 대응
                if "iframe" in site.message_selector:
                    iframe_id = site.message_selector.replace("iframe", "").replace("#", "").strip()
                    try:
                        frame = page.frame_locator(f"#{iframe_id}")
                        frame.locator("body").fill("[KEEPY_TEST] 자동 점검 메시지입니다. (Iframe)")
                    except:
                        # 일반 입력도 시도
                        page.fill(site.message_selector, "[KEEPY_TEST] 자동 점검 메시지입니다")
                else:
                    page.fill(site.message_selector, "[KEEPY_TEST] 자동 점검 메시지입니다")
            
            # 3. 제출 버튼 클릭
            if site.submit_selector:
                # 민병원 등 일부 사이트는 submit 버튼이 input type="image"인 경우가 있어 force 클릭 고려
                page.click(site.submit_selector, timeout=5000)
            else:
                page.keyboard.press("Enter")
                
            # 페이지 전환 및 응답 대기
            page.wait_for_timeout(3000)
            
            # 4. 성공 여부 판단
            content = page.content()
            
            # 스크린샷 저장
            screenshot_filename = f"site_{site.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = os.path.join("app", "static", "screenshots", screenshot_filename)
            page.screenshot(path=screenshot_path)
            # DB 저장용 상대 경로
            db_screenshot_path = f"screenshots/{screenshot_filename}"

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
        db_screenshot_path = None
        logger.debug(f"상담폼 체크 실패: site_id={site.id} 사유={fail_reason}")

    log = Log(
        site_id=site.id,
        check_type="form",
        status=status,
        response_time=response_time,
        fail_reason=fail_reason,
        raw_result=None,
        screenshot_path=db_screenshot_path if 'db_screenshot_path' in locals() else None
    )
    db.add(log)
    db.commit()
    return log
