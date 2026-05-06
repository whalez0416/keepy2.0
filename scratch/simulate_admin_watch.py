import sys
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from app.db import SessionLocal, engine, Base
from app.models import Site, Log, Alert, Organization
from app.services.admin_watcher import check_admin_exposure

# Mock Server Logic
class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # /admin 경로 접근 시 시뮬레이션 상태에 따라 응답
        if self.path == "/admin":
            if getattr(self.server, 'is_locked', False):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden: IP not allowed")
            else:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Admin Login</h1><form>...</form></body></html>")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Normal Page")
    
    def log_message(self, format, *args):
        return

def run_mock_server():
    server = HTTPServer(('localhost', 6666), MockHandler)
    server.is_locked = False # 초기값은 노출 상태
    print("[MOCK] 시뮬레이션 서버가 http://localhost:6666 에서 시작되었습니다.")
    global mock_server_instance
    mock_server_instance = server
    server.serve_forever()

def run_simulation():
    # 1. 서버 시작
    server_thread = threading.Thread(target=run_mock_server, daemon=True)
    server_thread.start()
    time.sleep(2)

    # 2. DB 초기화
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 3. 데이터 준비
        org = db.query(Organization).filter(Organization.slug == "admin-org").first()
        if not org:
            org = Organization(name="어드민 테스트 조직", slug="admin-org")
            db.add(org)
            db.flush()
        
        test_url = "http://localhost:6666"
        site = db.query(Site).filter(Site.homepage_url == test_url).first()
        if not site:
            site = Site(org_id=org.id, site_name="어드민 테스트 병원", homepage_url=test_url, admin_path="/admin")
            db.add(site)
            db.commit()
            print("[SETUP] 테스트 데이터 준비 완료.")

        # ---------------------------------------------------------
        # 시나리오 1: 관리자 페이지가 노출된 상황 (위험)
        # ---------------------------------------------------------
        print("\n[시나리오 1] 관리자 페이지 노출 탐지 테스트")
        mock_server_instance.is_locked = False
        log1 = check_admin_exposure(db, site)
        
        print(f"▶ 결과: {log1.status}")
        print(f"▶ 상세: {log1.fail_reason}")
        
        alert = db.query(Alert).filter(Alert.site_id == site.id, Alert.check_type == "admin_exposure").order_by(Alert.id.desc()).first()
        if log1.status == "warning" and alert:
            print("✅ 결과: 노출 위험을 성공적으로 탐지하고 경고를 생성했습니다.")
        else:
            print("❌ 결과: 노출 탐지에 실패했습니다.")

        # ---------------------------------------------------------
        # 시나리오 2: 관리자 페이지가 IP로 차단된 상황 (안전)
        # ---------------------------------------------------------
        print("\n[시나리오 2] 관리자 페이지 보호 상황 테스트 (IP 차단됨)")
        mock_server_instance.is_locked = True
        log2 = check_admin_exposure(db, site)
        
        print(f"▶ 결과: {log2.status}")
        if log2.status == "success":
            print("✅ 결과: 보호 중인 상태(403 Forbidden)를 정상으로 판별했습니다.")
        else:
            print("❌ 결과: 보호 중인 상태를 정상으로 판별하지 못했습니다.")

    except Exception as e:
        print(f"❌ 시뮬레이션 중 오류 발생: {e}")
    finally:
        db.close()
        print("\n" + "=" * 50)
        print("시뮬레이션 테스트 종료")
        print("=" * 50)

if __name__ == "__main__":
    run_simulation()
