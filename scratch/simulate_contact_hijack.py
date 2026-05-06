import sys
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from app.db import SessionLocal, engine, Base
from app.models import Site, ContactConfig, Log, Alert, Organization
from app.services.contact_checker import check_contact

# 가상 홈페이지 HTML 컨텐츠
HTML_NORMAL = """
<html>
<head><title>민트병원 - 공식 홈페이지</title></head>
<body>
    <h1>Welcome to Mint Hospital</h1>
    <p>상담전화: <a href="tel:02-1234-5678">02-1234-5678</a></p>
    <p>카카오톡 상담: <a href="https://pf.kakao.com/_mint_official">채널 추가하기</a></p>
</body>
</html>
"""

HTML_HIJACKED = """
<html>
<head><title>민트병원 - 공식 홈페이지</title></head>
<body>
    <h1>Welcome to Mint Hospital</h1>
    <!-- 해커가 번호와 링크를 변조한 상황 -->
    <p>상담전화: <a href="tel:010-9999-8888">010-9999-8888</a></p>
    <p>카카오톡 상담: <a href="https://pf.kakao.com/_hacker_account">채널 추가하기</a></p>
</body>
</html>
"""

# 현재 서버가 응답할 HTML (시뮬레이션 중 변경 예정)
current_html = HTML_NORMAL

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(current_html.encode("utf-8"))
    
    def log_message(self, format, *args):
        return # 로그 출력 억제

def run_mock_server():
    server = HTTPServer(('localhost', 8888), MockHandler)
    print("[MOCK] 시뮬레이션 서버가 http://localhost:8888 에서 시작되었습니다.")
    server.serve_forever()

def run_simulation():
    global current_html
    
    print("=" * 50)
    print("🚀 연락처 가로채기 방지(Contact Hijack Guard) 시뮬레이션 테스트")
    print("=" * 50)

    # 1. 시뮬레이션 서버 시작
    server_thread = threading.Thread(target=run_mock_server, daemon=True)
    server_thread.start()
    time.sleep(2) # 서버가 안정적으로 뜰 때까지 대기

    # 2. DB 초기화 및 테스트 데이터 설정
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 테스트용 조직 생성
        org = db.query(Organization).filter(Organization.slug == "sim-org").first()
        if not org:
            org = Organization(name="시뮬레이션 조직", slug="sim-org")
            db.add(org)
            db.flush()
            
        # 테스트용 사이트 생성
        test_url = "http://localhost:8888"
        site = db.query(Site).filter(Site.homepage_url == test_url).first()
        if not site:
            site = Site(
                org_id=org.id, 
                site_name="테스트 병원", 
                homepage_url=test_url,
                is_active=True
            )
            db.add(site)
            db.flush()
            
        # 연락처 감시 설정 생성
        config = db.query(ContactConfig).filter(ContactConfig.site_id == site.id).first()
        if not config:
            config = ContactConfig(
                site_id=site.id,
                expected_phone="02-1234-5678",
                expected_kakao_url="pf.kakao.com/_mint_official",
                is_active=True
            )
            db.add(config)
            db.commit()
            print("[SETUP] 테스트 데이터 준비 완료.")
        
        # ---------------------------------------------------------
        # 시나리오 1: 정상 상황
        # ---------------------------------------------------------
        print("\n[시나리오 1] 정상 홈페이지 체크")
        current_html = HTML_NORMAL
        log = check_contact(db, config)
        
        print(f"▶ 체크 결과: {log.status}")
        if log.status == "success":
            print("✅ 결과: 정상 상황을 성공적으로 판별했습니다.")
        else:
            print(f"❌ 결과: 오류 발생 - {log.fail_reason}")

        # ---------------------------------------------------------
        # 시나리오 2: 연락처 변조 발생!
        # ---------------------------------------------------------
        print("\n[시나리오 2] 연락처 변조 발생 상황 (해커의 침입)")
        current_html = HTML_HIJACKED
        log = check_contact(db, config)
        
        print(f"▶ 체크 결과: {log.status}")
        print(f"▶ 탐지된 사유: {log.fail_reason}")
        
        # Alert 테이블에 제대로 들어갔는지 확인
        latest_alert = db.query(Alert).filter(Alert.site_id == site.id).order_by(Alert.id.desc()).first()
        
        if log.status == "fail" and latest_alert:
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
