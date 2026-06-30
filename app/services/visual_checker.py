import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat
from sqlalchemy.orm import Session
from ..models import Site, Log
from ..utils.logger import get_logger
from .browser_pool import browser_semaphore

logger = get_logger("visual_checker")

# 유사도가 이 값 미만이면 '변조 의심'. 병원 홈페이지는 메인 배너 슬라이드·팝업·
# 공지 등이 매일 바뀌므로(=픽셀 차이 큼) 임계값을 높게 두면 오경보가 쏟아진다.
# 실제 변조(해커가 페이지 전체를 갈아끼움)는 유사도가 매우 낮게 나오므로,
# 임계값을 낮춰 '전면적 변화'에만 반응하게 한다. (배너 회전 정도로는 안 울림)
VISUAL_SIMILARITY_THRESHOLD = 60.0

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
                # networkidle은 채팅위젯·트래커로 안 끝날 수 있어 타임아웃 명시(초과해도 진행)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                # 팝업 등이 뜰 수 있으므로 잠시 대기
                time.sleep(2)
                
                # 2. 스크린샷 캡처 (로그 화면 표시용 파일 + 비교용 바이트 둘 다 확보)
                current_bytes = page.screenshot(path=current_path)
                browser.close()

        # 3. 기준 이미지와 비교 — 기준 이미지는 DB(baseline_screenshot_data)에 보관한다.
        #    Render 디스크는 재배포 시 사라지므로 파일 경로 기준은 매 배포마다 리셋돼
        #    변조 탐지가 사실상 무력화됐다. DB 저장으로 기준이 영구 유지된다.
        baseline_bytes = site.baseline_screenshot_data
        if not baseline_bytes:
            # 기준 이미지가 없으면 현재 이미지를 기준으로 설정(DB 저장)
            site.baseline_screenshot_data = current_bytes
            db.commit()
            logger.info(f"기준 이미지 설정 완료(DB 저장): site_id={site.id}")
        else:
            similarity = compare_image_bytes(baseline_bytes, current_bytes)
            logger.debug(f"이미지 유사도: {similarity:.2f}%")

            # 임계값 미만이면 변조 의심 (배너/팝업 회전 정도로는 안 울리게 낮게 설정)
            if similarity < VISUAL_SIMILARITY_THRESHOLD:
                status = "warning"
                fail_reason = (
                    f"⚠️ [화면 변화 감지 · 베타] 홈페이지 화면이 평소와 크게 다릅니다 "
                    f"(유사도 {similarity:.2f}%). 디자인 개편·배너 교체일 수도 있으니 "
                    f"육안으로 확인해 주세요. 실제 개편이라면 기준 이미지를 갱신하면 됩니다."
                )
                # Alert 생성/이메일은 스케줄러가 handle_check_result로 일원화 처리한다.
                logger.warning(f"ALERT: 비주얼 변조 의심! site_id={site.id} similarity={similarity:.2f}%")

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

def _similarity(img1, img2):
    """두 PIL 이미지의 유사도(%)를 RMS 차이 기반으로 계산."""
    img1 = img1.convert('RGB')
    img2 = img2.convert('RGB')
    # 크기가 다르면 맞춤 (보통 같은 URL이면 같아야 함)
    if img1.size != img2.size:
        img2 = img2.resize(img1.size)
    diff = ImageChops.difference(img1, img2)
    stat = ImageStat.Stat(diff)
    # RMS 차이가 작을수록 유사. 완전 일치=0, 완전 상이≈255.
    sum_rms = sum(stat.rms) / 3.0
    return max(0, 100 - (sum_rms / 255.0 * 100))


def compare_images(path1, path2):
    """두 이미지 파일의 유사도를 퍼센트로 반환."""
    return _similarity(Image.open(path1), Image.open(path2))


def compare_image_bytes(bytes1, bytes2):
    """두 이미지(PNG 바이트)의 유사도를 퍼센트로 반환."""
    import io
    return _similarity(Image.open(io.BytesIO(bytes1)), Image.open(io.BytesIO(bytes2)))
