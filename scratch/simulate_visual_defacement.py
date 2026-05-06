import sys
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from app.db import SessionLocal, engine, Base
from app.models import Site, Log, Alert, Organization
from app.services.visual_checker import check_visual_defacement

# 가상 홈페이지 HTML 컨텐츠
HTML_NORMAL = """
<html>
<head><title>민트병원</title></head>
<body style="background-color: white; font-family: sans-serif; padding: 50px;">
    <h1 style="color: #2ecc71;">Mint Hospital</h1>
    <p>We provide the best healthcare services.</p>
    <div style="width: 200px; height: 100px; background-color: #3498db; margin-top: 20px;">
        Our Mission
    </div>
</body>
</html>
"""

HTML_DEFACED = """
<html>
<head><title>HACKED BY KEEPY</title></head>
<body style="background-color: black; color: red; font-family: serif; padding: 50px;">
    <h1>HACKED BY KEEPY</h1>
    <p>Your site is under our control.</p>
    <div style="width: 200px; height: 100px; background-color: yellow; margin-top: 20px;">
        !!! HACKED !!!
    </div>
</body>
</html>
"""

current_html = HTML_NORMAL

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(current_html.encode("utf-8"))
    
    def log_message(self, format, *args):
        return

def run_mock_server():
    server = HTTPServer(('localhost', 9999), MockHandler)
    print("[MOCK] 시뮬레이션 서버가 http://localhost:9999 에서 시작되었습니다.")
    server.serve_forever()

def run_simulation():
    global current_html
    
    print("=" * 50)
    print("🚀 홈페이지 비주얼 변조 탐지(Visual Defacement) 시뮬레이션 테스트")
    print("=" * 50)

    # 1. 서버 시작
    server_thread = threading.Thread(target=run_mock_server, daemon=True)
    server_thread.start()
    time.sleep(2)

    # 2. DB 초기화
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 3. 데이터 준비
        org = db.query(Organization).filter(Organization.slug == "visual-org").first()
        if not org:
            org = Organization(name="비주얼 테스트 조직", slug="visual-org")
            db.add(org)
            db.flush()
        
        test_url = "http://localhost:9999"
        site = db.query(Site).filter(Site.homepage_url == test_url).first()
        if not site:
            site = Site(org_id=org.id, site_name="비주얼 테스트 병원", homepage_url=test_url)
            db.add(site)
            db.commit()
            print("[SETUP] 테스트 사이트 생성 완료.")

        # ---------------------------------------------------------
        # 시나리오 1: 최초 실행 (기준 이미지 설정)
        # ---------------------------------------------------------
        print("\n[시나리오 1] 최초 실행 - 기준(Baseline) 이미지 생성")
        current_html = HTML_NORMAL
        # 기존 기준 이미지가 있다면 초기화 (테스트를 위해)
        site.baseline_screenshot_path = None
        db.commit()
        
        log1 = check_visual_defacement(db, site)
        print(f"▶ 결과: {log1.status}")
        if site.baseline_screenshot_path:
            print(f"✅ 기준 이미지가 성공적으로 저장되었습니다: {site.baseline_screenshot_path}")

        # ---------------------------------------------------------
        # 시나리오 2: 정상 상황 재방문
        # ---------------------------------------------------------
        print("\n[시나리오 2] 정상 상황 재방문 (유사도 체크)")
        log2 = check_visual_defacement(db, site)
        print(f"▶ 결과: {log2.status} (유사도: {log2.raw_result})")
        if log2.status == "success":
            print("✅ 정상 상태를 성공적으로 판별했습니다.")

        # ---------------------------------------------------------
        # 시나리오 3: 변조 발생!
        # ---------------------------------------------------------
        print("\n[시나리오 3] 화면 변조 발생 상황 (해킹 모의)")
        current_html = HTML_DEFACED
        log3 = check_visual_defacement(db, site)
        
        print(f"▶ 결과: {log3.status} (유사도: {log3.raw_result})")
        
        latest_alert = db.query(Alert).filter(Alert.site_id == site.id, Alert.check_type == "visual_defacement").order_by(Alert.id.desc()).first()
        
        if log3.status == "warning" and latest_alert:
            print("✅ 결과: 변조를 즉시 탐지하고 경고(Alert)를 생성했습니다!")
            print(f"🔔 알림 메시지: {latest_alert.message}")
        else:
            print("❌ 결과: 변조 탐지에 실패했거나 알림이 생성되지 않았습니다.")

    except Exception as e:
        print(f"❌ 시뮬레이션 중 오류 발생: {e}")
    finally:
        db.close()
        print("\n" + "=" * 50)
        print("시뮬레이션 테스트 종료")
        print("=" * 50)

if __name__ == "__main__":
    run_simulation()
