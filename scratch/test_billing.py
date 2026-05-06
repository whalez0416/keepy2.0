import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_billing():
    # 1. Login as Master
    login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": "master@keepy.com", "password": "keepy1234"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Org ID (Mint Hospital is likely 1)
    org_res = requests.get(f"{BASE_URL}/organizations/", headers=headers)
    org_id = org_res.json()[0]["id"]
    org_name = org_res.json()[0]["name"]
    print(f"Testing for Org: {org_name} (ID: {org_id})")
    
    # 2. Check Status
    status_res = requests.get(f"{BASE_URL}/billing/status/{org_id}", headers=headers)
    print(f"Initial Status: {status_res.json()}")
    
    # 3. Subscribe to Pro
    sub_res = requests.post(f"{BASE_URL}/billing/subscribe/{org_id}?plan=pro", headers=headers)
    print(f"Subscribe Result: {sub_res.json()}")
    
    # 4. Check Status again
    status_res2 = requests.get(f"{BASE_URL}/billing/status/{org_id}", headers=headers)
    print(f"Final Status: {status_res2.json()}")

if __name__ == "__main__":
    try:
        test_billing()
    except Exception as e:
        print(f"Test failed: {e}")
