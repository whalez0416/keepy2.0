
import os
import sys
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.scheduler_service import run_site_check

def run_test_check():
    db = SessionLocal()
    site_id = 7 # The one I just added
    print(f"Running manual check for site {site_id}...")
    try:
        run_site_check(site_id, "homepage")
        print("Homepage check completed.")
    except Exception as e:
        print(f"Homepage check failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure app directory is in path
    sys.path.append(os.getcwd())
    run_test_check()
