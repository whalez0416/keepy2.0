import requests
import json
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BASE_URL = "http://127.0.0.1:8000"
DB_URL = "sqlite:///./keepy.db"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def cleanup_db():
    print("[TEST] Cleaning up database...")
    db = SessionLocal()
    db.execute(text("DELETE FROM alerts"))
    db.execute(text("DELETE FROM logs"))
    db.execute(text("DELETE FROM sites"))
    db.commit()
    db.close()

def test_scenario_1_normal():
    print("\n--- 시나리오 1: 정상 상황 테스트 ---")
    # Using a reliable site like google for homepage check
    site_data = {
        "site_name": "정상 사이트",
        "homepage_url": "https://www.google.com",
        "form_url": None,
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    # Run manual check
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    
    db = SessionLocal()
    logs = db.execute(text(f"SELECT status FROM logs WHERE site_id={site_id}")).fetchall()
    alerts = db.execute(text(f"SELECT * FROM alerts WHERE site_id={site_id}")).fetchall()
    db.close()
    
    print(f"로그 결과: {[l[0] for l in logs]}")
    print(f"알림 생성 개수: {len(alerts)}")
    
    if len(alerts) == 0 and all(l[0] == "success" for l in logs):
        print("결과: PASS")
    else:
        print("결과: FAIL")

def test_scenario_2_homepage_fail():
    print("\n--- 시나리오 2: 홈페이지 장애 테스트 (2회 연속 실패 시 알림) ---")
    site_data = {
        "site_name": "장애 사이트",
        "homepage_url": "https://this-url-does-not-exist-keepy-test.com",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    print("1회차 점검 실행...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    db = SessionLocal()
    alerts = db.execute(text(f"SELECT * FROM alerts WHERE site_id={site_id}")).fetchall()
    print(f"1회 실패 후 알림 개수: {len(alerts)}")
    
    print("2회차 점검 실행...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    alerts = db.execute(text(f"SELECT * FROM alerts WHERE site_id={site_id}")).fetchall()
    print(f"2회 연속 실패 후 알림 개수: {len(alerts)}")
    db.close()
    
    if len(alerts) == 1:
        print("결과: PASS")
    else:
        print("결과: FAIL")

def test_scenario_3_form_fail():
    print("\n--- 시나리오 3: 상담폼 실패 테스트 (1회 실패 시 즉시 알림) ---")
    site_data = {
        "site_name": "폼 장애 사이트",
        "homepage_url": "https://www.google.com",
        "form_url": "https://www.google.com/contact-fake", # URL exists but no form
        "name_selector": "#invalid-selector",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    print("폼 점검 실행...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    
    db = SessionLocal()
    logs = db.execute(text(f"SELECT status, fail_reason FROM logs WHERE site_id={site_id} AND check_type='form'")).fetchall()
    alerts = db.execute(text(f"SELECT * FROM alerts WHERE site_id={site_id} AND check_type='form'")).fetchall()
    db.close()
    
    print(f"폼 로그 결과: {logs}")
    print(f"폼 알림 생성 개수: {len(alerts)}")
    
    if len(alerts) >= 1:
        print("결과: PASS")
    else:
        print("결과: FAIL")

def test_scenario_4_false_positive():
    print("\n--- 시나리오 4: 가짜 성공 테스트 (HTTP 200이나 성공 메시지 없음) ---")
    site_data = {
        "site_name": "가짜 성공 사이트",
        "homepage_url": "https://www.google.com",
        "form_url": "https://www.google.com", # Page exists but no success text
        "expected_success_text": "절대로나올수없는성공메시지123",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    print("폼 점검 실행...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    
    db = SessionLocal()
    logs = db.execute(text(f"SELECT status FROM logs WHERE site_id={site_id} AND check_type='form'")).fetchall()
    db.close()
    
    print(f"폼 로그 결과: {[l[0] for l in logs]}")
    
    if any(l[0] == "fail" for l in logs):
        print("결과: PASS (가짜 성공을 실패로 잘 포착함)")
    else:
        print("결과: FAIL (가짜 성공을 걸러내지 못함)")

def test_scenario_5_cooldown():
    print("\n--- 시나리오 5: 알림 중복 방지 테스트 (1시간 이내) ---")
    site_data = {
        "site_name": "중복 방지 테스트",
        "homepage_url": "https://www.google.com",
        "form_url": "https://www.google.com/fake-url-404",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    print("1차 실패 유도 (알림 발생 기대)...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    
    db = SessionLocal()
    alerts_1 = db.execute(text(f"SELECT * FROM alerts WHERE site_id={site_id}")).fetchall()
    print(f"1차 후 알림 개수: {len(alerts_1)}")
    
    print("2차 즉시 실패 유도 (중복 알림 차단 기대)...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    alerts_2 = db.execute(text(f"SELECT * FROM alerts WHERE site_id={site_id}")).fetchall()
    print(f"2차 후 알림 개수: {len(alerts_2)}")
    db.close()
    
    if len(alerts_2) == 1:
        print("결과: PASS (중복 알림 억제됨)")
    else:
        print("결과: FAIL (중복 알림 발생)")

def test_scenario_6_slow_response():
    print("\n--- 시나리오 6: 응답 지연 테스트 (3초 초과 시 warning) ---")
    # Using a slow mock or long-loading URL if available, 
    # but here we'll mock the response check via database if we can't find a real slow one.
    # We can use a service like 'https://httpbin.org/delay/4'
    site_data = {
        "site_name": "지연 사이트",
        "homepage_url": "https://httpbin.org/delay/4",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    print("지연 점검 실행 (약 4~5초 대기)...")
    requests.post(f"{BASE_URL}/checks/run/{site_id}")
    
    db = SessionLocal()
    logs = db.execute(text(f"SELECT status, response_time FROM logs WHERE site_id={site_id}")).fetchall()
    db.close()
    
    print(f"로그 결과: {logs}")
    
    if any(l[0] == "warning" for l in logs):
        print("결과: PASS (지연 발생 시 warning 처리됨)")
    else:
        print("결과: FAIL (지연을 감지하지 못함)")

def test_scenario_7_deactivation():
    print("\n--- 시나리오 7: 사이트 비활성화 테스트 ---")
    site_data = {
        "site_name": "삭제 예정 사이트",
        "homepage_url": "https://www.google.com",
        "is_active": True
    }
    resp = requests.post(f"{BASE_URL}/sites/", json=site_data)
    site_id = resp.json()["id"]
    
    # Deactivate
    print("사이트 비활성화 실행...")
    requests.delete(f"{BASE_URL}/sites/{site_id}")
    
    db = SessionLocal()
    site = db.execute(text(f"SELECT is_active FROM sites WHERE id={site_id}")).fetchone()
    db.close()
    
    print(f"DB 활성 상태: {site[0]}")
    
    if site[0] == 0: # 0 is False in SQLite
        print("결과: PASS (비활성화 처리 완료)")
    else:
        print("결과: FAIL (비활성화 실패)")

if __name__ == "__main__":
    # Note: Make sure the server is running on 127.0.0.1:8000
    try:
        cleanup_db()
        test_scenario_1_normal()
        test_scenario_2_homepage_fail()
        test_scenario_3_form_fail()
        test_scenario_4_false_positive()
        test_scenario_5_cooldown()
        test_scenario_6_slow_response()
        test_scenario_7_deactivation()
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
