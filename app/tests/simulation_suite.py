import uvicorn
from fastapi import FastAPI, Response, Request
from multiprocessing import Process, Manager, freeze_support
import time
import requests
import json
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# --- MOCK TARGET WEBSITE ---
mock_app = FastAPI()

# Global shared_state will be initialized in main
shared_state = None

@mock_app.get("/")
async def root():
    global shared_state
    if shared_state["delay"] > 0:
        time.sleep(shared_state["delay"])
    return Response(content=shared_state["content"], media_type="text/html", status_code=shared_state["status_code"])

@mock_app.post("/control")
async def control(config: dict):
    global shared_state
    shared_state.update(config)
    return dict(shared_state)

def run_mock_server(shared_state_in):
    global shared_state
    shared_state = shared_state_in
    uvicorn.run(mock_app, host="127.0.0.1", port=9998, log_level="error")

# --- SIMULATION RUNNER ---
BASE_URL = "http://127.0.0.1:8000"
DB_URL = "sqlite:///./keepy.db"
MOCK_SITE_URL = "http://127.0.0.1:9998"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def set_mock_state(status_code=200, delay=0, content=None):
    data = {"status_code": status_code, "delay": delay}
    if content:
        data["content"] = content
    requests.post(f"{MOCK_SITE_URL}/control", json=data)

def get_auth_token():
    print("[SIM] Authenticating as master...")
    resp = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": "master@keepy.com",
        "password": "keepy1234"
    })
    return resp.json()["access_token"]

def setup_test_site(token):
    print("[SIM] Setting up test site via API...")
    headers = {"Authorization": f"Bearer {token}"}
    db = SessionLocal()
    db.execute(text("DELETE FROM logs WHERE site_id IN (SELECT id FROM sites WHERE site_name='Simulation Target')"))
    db.execute(text("DELETE FROM alerts WHERE site_id IN (SELECT id FROM sites WHERE site_name='Simulation Target')"))
    db.execute(text("DELETE FROM sites WHERE site_name='Simulation Target'"))
    db.commit()
    db.close()

    site_data = {
        "site_name": "Simulation Target",
        "homepage_url": MOCK_SITE_URL,
        "is_active": True,
        "expected_phone": "02-1111-2222",
        "expected_kakao_url": "https://pf.kakao.com/original"
    }
    resp = requests.post(f"{BASE_URL}/api/sites/", json=site_data, headers=headers)
    return resp.json()["id"]

def trigger_check(site_id, token):
    print(f"[SIM] Triggering check for site {site_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/checks/run/{site_id}", headers=headers)
    return resp.json()

def verify_results(site_id, expected_status, check_type="homepage"):
    time.sleep(2) # Give more time for Playwright checks
    db = SessionLocal()
    # Search for logs matching check_type prefix
    last_log = db.execute(text(f"SELECT status, fail_reason FROM logs WHERE site_id={site_id} AND check_type LIKE '{check_type}%' ORDER BY checked_at DESC LIMIT 1")).fetchone()
    db.close()
    
    print(f"  > [{check_type}] Last Log: {last_log}")
    
    if last_log and last_log[0] == expected_status:
        return True
    return False

def run_scenarios(site_id, token):
    print("\n" + "="*50)
    print("KEEPY 1.0 SIMULATION SUITE START")
    print("="*50)

    # Scenario 1: Normal Operation
    print("\n[Scenario 1] Normal Operation")
    set_mock_state(status_code=200, delay=0, content="<html><body><h1>Hospital</h1><p><a href='tel:02-1111-2222'>Phone</a></p><a href='https://pf.kakao.com/original'>Kakao</a></body></html>")
    trigger_check(site_id, token)
    verify_results(site_id, "success", "homepage")
    verify_results(site_id, "success", "visual")
    verify_results(site_id, "success", "contact")

    # Scenario 2: Server Down (500 Error)
    print("\n[Scenario 2] Server Down (500 Error)")
    set_mock_state(status_code=500)
    trigger_check(site_id, token)
    verify_results(site_id, "fail", "homepage")

    # Scenario 3: Slow Response
    print("\n[Scenario 3] Slow Response (Latency Stress)")
    set_mock_state(status_code=200, delay=4) 
    trigger_check(site_id, token)
    verify_results(site_id, "warning", "homepage")

    # Scenario 4: Visual Defacement
    print("\n[Scenario 4] Visual Defacement")
    set_mock_state(status_code=200, delay=0, content="<html><body style='background: red;'><h1>HACKED</h1><marquee>YOU ARE HACKED</marquee></body></html>")
    trigger_check(site_id, token)
    verify_results(site_id, "warning", "visual")

    # Scenario 5: Contact Hijack
    print("\n[Scenario 5] Contact Hijack")
    set_mock_state(content="<html><body><h1>Hospital</h1><p><a href='tel:02-9999-9999'>Phone</a></p><a href='https://pf.kakao.com/hacker'>Kakao</a></body></html>")
    trigger_check(site_id, token)
    verify_results(site_id, "fail", "contact")

    print("\n" + "="*50)
    print("SIMULATION COMPLETED")
    print("="*50)

if __name__ == "__main__":
    freeze_support()
    manager = Manager()
    shared_state_obj = manager.dict({
        "status_code": 200,
        "delay": 0,
        "content": "<html><body><h1>Hospital</h1></body></html>"
    })
    
    p = Process(target=run_mock_server, args=(shared_state_obj,))
    p.start()
    time.sleep(2) 
    
    try:
        token = get_auth_token()
        site_id = setup_test_site(token)
        run_scenarios(site_id, token)
    except Exception as e:
        print(f"[SIM] Error: {e}")
    finally:
        print("[SIM] Shutting down mock server...")
        p.terminate()
        p.join()
