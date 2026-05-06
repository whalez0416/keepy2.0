import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_user(email, password, label):
    print(f"\n--- Testing for {label} ({email}) ---")
    
    # 1. Login
    login_res = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    if login_res.status_code != 200:
        print(f"Login failed: {login_res.text}")
        return
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Organizations
    orgs_res = requests.get(f"{BASE_URL}/organizations/", headers=headers)
    print(f"Organizations: {[o['name'] for o in orgs_res.json()]}")
    
    # 3. Get Sites
    sites_res = requests.get(f"{BASE_URL}/sites/", headers=headers)
    print(f"Sites: {[s['site_name'] for s in sites_res.json()]}")

if __name__ == "__main__":
    # Note: Backend must be running at http://localhost:8000
    try:
        test_user("master@keepy.com", "keepy1234", "MASTER")
        test_user("user@mint.com", "user1234", "REGULAR USER")
    except Exception as e:
        print(f"Test failed: {e}. Is the server running?")
