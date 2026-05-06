import sys
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from playwright.sync_api import sync_playwright

# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

# 1. 통합 시뮬레이션 서버 (API + 정적 파일 + 가상 병원 홈페이지)
class MockServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # (1) 배너 JS 스크립트 제공
        if self.path == "/static/keepy-banner.js":
            try:
                with open("app/static/keepy-banner.js", "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-type", "application/javascript")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "File Not Found")
        
        # (2) 공개 API 상태값 제공
        elif "/api/sites/public/" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*") # CORS 허용
            self.end_headers()
            
            # URL 쿼리에 'active=true'가 포함되어 있으면 활성 상태로 응답
            is_active = "active=true" in self.path
            msg = "현재 긴급 서버 점검 중입니다. 이용에 불편을 드려 죄송합니다. (문의: 02-1234-5678)"
            
            import json
            response = {"active": is_active, "message": msg}
            self.wfile.write(json.dumps(response).encode())

        # (3) 가상의 병원 홈페이지 제공
        elif self.path.startswith("/hospital"):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            # 테스트를 위해 data-site-id에 active 여부를 파라미터로 넘김
            is_on = "mode=on" in self.path
            site_id = f"5?active={'true' if is_on else 'false'}"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>민트병원 공식 홈페이지</title>
                <style>
                    body {{ font-family: sans-serif; margin: 0; padding: 20px; }}
                    header {{ background: #eee; padding: 20px; text-align: center; }}
                    main {{ padding: 40px; line-height: 1.6; }}
                </style>
            </head>
            <body>
                <header><h1>MINT HOSPITAL</h1></header>
                <main>
                    <h2>안녕하세요, 민트병원입니다.</h2>
                    <p>우리 병원은 최고의 의료 서비스를 제공하기 위해 최선을 다하고 있습니다.</p>
                </main>
                <!-- Keepy 긴급 배너 스크립트 삽입 -->
                <script src="/static/keepy-banner.js" data-site-id="{site_id}" data-api-base="http://localhost:7777"></script>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
    
    def log_message(self, format, *args):
        return

def run_server():
    server = HTTPServer(('localhost', 7777), MockServerHandler)
    print("[MOCK] 통합 시뮬레이션 서버가 http://localhost:7777 에서 시작되었습니다.")
    server.serve_forever()

def run_simulation():
    # 1. 서버 시작
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    
    print("=" * 50)
    print("🚀 긴급 안내 배너(Emergency Banner) 시뮬레이션 테스트")
    print("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # ---------------------------------------------------------
        # 시나리오 1: 배너 비활성 상태 (평상시)
        # ---------------------------------------------------------
        print("\n[시나리오 1] 배너 비활성 상태 (평상시)")
        page.goto("http://localhost:7777/hospital?mode=off")
        time.sleep(3) # 스크립트 실행 대기
        
        banner = page.query_selector("#keepy-emergency-banner")
        if not banner:
            print("✅ 결과: 배너가 나타나지 않았습니다. (정상)")
        else:
            print("❌ 결과: 비활성 상태인데 배너가 화면에 표시되었습니다.")

        # ---------------------------------------------------------
        # 시나리오 2: 배너 활성 상태 (긴급 상황)
        # ---------------------------------------------------------
        print("\n[시나리오 2] 배너 활성 상태 (긴급 점검 중)")
        page.goto("http://localhost:7777/hospital?mode=on")
        time.sleep(3) # 스크립트 실행 대기
        
        banner = page.query_selector("#keepy-emergency-banner")
        if banner:
            text = banner.inner_text()
            print(f"✅ 결과: 배너가 성공적으로 화면에 나타났습니다!")
            print(f"🔔 배너 문구: {text.replace('📢', '').strip()}")
            
            # 스타일 검증 (상단 고정 여부 등)
            position = page.evaluate("el => getComputedStyle(el).position", banner)
            if position == "fixed":
                print("✅ 결과: 상단 고정(position: fixed) 스타일이 올바르게 적용되었습니다.")
        else:
            print("❌ 결과: 활성 상태임에도 배너가 나타나지 않았습니다.")
            
        browser.close()

if __name__ == "__main__":
    run_simulation()
