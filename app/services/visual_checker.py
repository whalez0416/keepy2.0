import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat
from sqlalchemy.orm import Session
from ..models import Site, Log, Alert
from ..utils.logger import get_logger
from .browser_pool import browser_semaphore

logger = get_logger("visual_checker")

def check_visual_defacement(db: Session, site: Site):
    """
    홈페이지의 시각적 변화를 탐지합니다.
    """
    logger.debug(f"비주얼 변조 체크 시작: site_id={site.id} url={site.homepage_url}")
    
    start_time = time.time()
    status = "success"
    fail_reason = None
    similarity = 100.0
    
    screenshot_dir = os.path.join("app", "static", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    current_filename = f"site_{site.id}_visual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    current_path = os.path.join(screenshot_dir, current_filename)
    db_current_path = f"screenshots/{current_filename}"

    try:
        with browser_semaphore:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1280, 'height': 800})
                
                # 1. 페이지 로드
                page.goto(site.homepage_url, timeout=30000)
                page.wait_for_load_state("networkidle")
                # 팝업 등이 뜰 수 있으므로 잠시 대기
                time.sleep(2)
                
                # 2. 스크린샷 캡처
                page.screenshot(path=current_path)
                browser.close()

        # 3. 기준 이미지와 비교
        if not site.baseline_screenshot_path:
            # 기준 이미지가 없으면 현재 이미지를 기준으로 설정
            site.baseline_screenshot_path = db_current_path
            db.commit()
            logger.info(f"기준 이미지 설정 완료: site_id={site.id}")
        else:
            # 이미지 비교 로직
            baseline_full_path = os.path.join("app", "static", site.baseline_screenshot_path)
            
            if os.path.exists(baseline_full_path):
                similarity = compare_images(baseline_full_path, current_path)
                logger.debug(f"이미지 유사도: {similarity:.2f}%")
                
                # 유사도가 90% 미만이면 변조 의심
                if similarity < 90.0:
                    status = "warning"
                    fail_reason = f"시각적 변조 의심 (유사도: {similarity:.2f}%)"
                    
                    # 알림 생성
                    alert = Alert(
                        site_id=site.id,
                        check_type="visual_defacement",
                        alert_level="warning",
                        message=f"⚠️ [변조 의심] 홈페이지 화면이 평소와 다릅니다. (유사도: {similarity:.2f}%)"
                    )
                    db.add(alert)
                    logger.warning(f"ALERT: 비주얼 변조 의심! site_id={site.id} similarity={similarity:.2f}%")
            else:
                logger.error(f"기준 이미지를 찾을 수 없습니다: {baseline_full_path}")
                site.baseline_screenshot_path = db_current_path # 다시 설정
                db.commit()

    except Exception as e:
        status = "fail"
        fail_reason = str(e)
        logger.error(f"비주얼 체크 실패: {e}")

    # 로그 기록
    log = Log(
        site_id=site.id,
        check_type="visual_defacement",
        status=status,
        response_time=time.time() - start_time,
        fail_reason=fail_reason,
        screenshot_path=db_current_path,
        raw_result=f"Similarity: {similarity:.2f}%"
    )
    db.add(log)
    db.commit()
    
    return log

def compare_images(path1, path2):
    """
    두 이미지의 유사도를 퍼센트로 반환합니다.
    """
    img1 = Image.open(path1).convert('RGB')
    img2 = Image.open(path2).convert('RGB')
    
    # 크기가 다르면 맞춤 (보통 같은 URL이면 같아야 함)
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)
    
    # 차이 계산
    diff = ImageChops.difference(img1, img2)
    stat = ImageStat.Stat(diff)
    
    # 통계 기반 유사도 계산 (RMS 차이가 작을수록 유사함)
    # 완전 일치하면 0, 완전히 다르면 약 255
    sum_rms = sum(stat.rms) / 3.0
    similarity = max(0, 100 - (sum_rms / 255.0 * 100))
    
    return similarity
