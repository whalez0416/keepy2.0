import json
from playwright.sync_api import sync_playwright
import time
from sqlalchemy.orm import Session
import os
from datetime import datetime
from ..models import Site, Log, FormConfig
from ..utils.logger import get_logger
from .browser_pool import browser_semaphore

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

def check_form(db: Session, form_config: FormConfig):
    if not form_config or not form_config.form_url:
        logger.debug(f"상담폼 체크 건너뜀: form_config_id={form_config.id if form_config else 'None'}")
        return None

    site = form_config.site
    logger.debug(f"상담폼 체크 시작: site_id={site.id} form_name={form_config.name} url={form_config.form_url}")
    
    start_time = time.time()
    status = "fail"
    fail_reason = None
    db_screenshot_path = None
    
    try:
        with browser_semaphore:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                # JS alert/confirm 메시지 캡처 (많은 게시판이 '등록되었습니다' 등을
                # alert로 띄우고 리다이렉트한다 — content엔 안 남으므로 따로 수집).
                dialog_messages = []

                def _on_dialog(dialog):
                    try:
                        dialog_messages.append(dialog.message or "")
                        dialog.accept()
                    except Exception:
                        pass

                page.on("dialog", _on_dialog)

                # 1. 상담 페이지 이동
                page.goto(form_config.form_url, timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # 1.5. 팝업 제거
                try:
                    page.evaluate("() => { if(typeof layer_close_all2 === 'function') layer_close_all2(); }")
                    page.evaluate("() => { document.querySelectorAll('.btn_close, .close_btn, #close, [title=\"닫기\"]').forEach(el => el.click()); }")
                    page.wait_for_timeout(1000)
                except:
                    pass

                # 1.6. 고급 액션 시퀀스 실행 (사이트 공통 설정)
                if site.extra_steps_json:
                    logger.debug(f"[ADVANCED] 사이트 {site.id}의 고급 액션 시퀀스를 시작합니다.")
                    execute_extra_steps(page, site.extra_steps_json)

                # 2. 테스트 데이터 입력
                if form_config.name_selector:
                    page.fill(form_config.name_selector, "KEEPY_TEST")
                
                if form_config.phone_selector:
                    page.fill(form_config.phone_selector, "01000000000")
                
                if form_config.subject_selector:
                    page.fill(form_config.subject_selector, f"[KEEPY_TEST] {form_config.name} 자동 점검")
                
                if form_config.password_selector:
                    pass_val = form_config.password_value or "keepy1234!"
                    page.fill(form_config.password_selector, pass_val)

                if form_config.agreement_selector:
                    try:
                        page.click(form_config.agreement_selector)
                    except:
                        page.click(form_config.agreement_selector, force=True)

                if form_config.message_selector:
                    if "iframe" in form_config.message_selector:
                        iframe_id = form_config.message_selector.replace("iframe", "").replace("#", "").strip()
                        try:
                            frame = page.frame_locator(f"#{iframe_id}")
                            frame.locator("body").fill("[KEEPY_TEST] 자동 점검 메시지입니다. (Iframe)")
                        except:
                            page.fill(form_config.message_selector, "[KEEPY_TEST] 자동 점검 메시지입니다")
                    else:
                        page.fill(form_config.message_selector, "[KEEPY_TEST] 자동 점검 메시지입니다")
                
                # 3. 제출 버튼 클릭
                pre_submit_url = page.url
                if form_config.submit_selector:
                    page.click(form_config.submit_selector, timeout=5000)
                else:
                    page.keyboard.press("Enter")

                page.wait_for_timeout(3000)

                # 4. 성공 여부 판단
                # 검색 대상: 페이지 본문 + alert로 떴던 메시지(리다이렉트로 사라지는 경우 대비)
                content = page.content() + " " + " ".join(dialog_messages)
                post_submit_url = page.url
                
                # 스크린샷 저장
                screenshot_dir = os.path.join("app", "static", "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_filename = f"site_{site.id}_form_{form_config.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
                page.screenshot(path=screenshot_path)
                db_screenshot_path = f"screenshots/{screenshot_filename}"

                if form_config.expected_success_text:
                    # 성공 문구가 설정돼 있으면 그것만으로 판정 (가장 신뢰도 높음)
                    if form_config.expected_success_text in content:
                        status = "success"
                    else:
                        status = "fail"
                        fail_reason = f"성공 메시지('{form_config.expected_success_text}')를 찾을 수 없습니다"
                else:
                    # 성공 문구 미설정 시 휴리스틱.
                    # 주의: '제출'은 제출 버튼 라벨로 거의 모든 페이지에 항상 존재하므로
                    # 성공 신호로 쓰면 폼 장애를 놓친다(false negative) → 사용하지 않는다.
                    SUCCESS_PHRASES = [
                        "등록되었습니다", "접수되었습니다", "정상적으로", "감사합니다",
                        "완료되었습니다", "등록 완료", "접수 완료", "신청이 완료",
                        "success", "thank you",
                    ]
                    ERROR_PHRASES = ["오류", "에러", "실패", "error", "필수", "입력해", "다시 시도"]

                    lower = content.lower()
                    has_success = any(p.lower() in lower for p in SUCCESS_PHRASES)
                    has_error = any(p.lower() in lower for p in ERROR_PHRASES)
                    # 제출 후 다른 URL(보기 페이지/완료 페이지)로 이동했는지
                    navigated = post_submit_url != pre_submit_url

                    if has_success or (navigated and not has_error):
                        status = "success"
                    else:
                        status = "fail"
                        fail_reason = (
                            "제출 후 성공 신호(완료 문구/페이지 이동)를 확인하지 못했습니다. "
                            "정확한 판정을 위해 폼 설정에 '성공 메시지'를 지정해 주세요."
                        )
                    
                browser.close()
            
        response_time = time.time() - start_time
        
    except Exception as e:
        response_time = time.time() - start_time
        status = "fail"
        fail_reason = str(e)
        logger.error(f"상담폼 체크 실패: site_id={site.id} form_id={form_config.id} 사유={fail_reason}")

    log = Log(
        site_id=site.id,
        check_type=f"form:{form_config.name}", # 어떤 폼인지 식별 가능하게 함
        status=status,
        response_time=response_time,
        fail_reason=fail_reason,
        raw_result=None,
        screenshot_path=db_screenshot_path
    )
    db.add(log)
    db.commit()
    return log
