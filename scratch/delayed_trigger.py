import sys
import os
import time

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Site, Organization

DB_URL = "sqlite:///../keepy.db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def reset_emergency():
    # first make sure it's off
    db = SessionLocal()
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Test Org", slug="test-org")
        db.add(org)
        db.commit()

    site = db.query(Site).filter(Site.id == 9).first()
    if not site:
        db.execute(text(f"INSERT INTO sites (id, org_id, site_name, homepage_url, emergency_mode_active, emergency_message, is_active) VALUES (9, {org.id}, 'Mock Hospital', 'http://localhost:8000/static/mock_hospital.html', 0, '', 1)"))
    else:
        site.emergency_mode_active = False
        site.emergency_message = ""
    db.commit()

def trigger_emergency():
    db = SessionLocal()
    site = db.query(Site).filter(Site.id == 9).first()
    site.emergency_mode_active = True
    site.emergency_message = "📢 [긴급 안내] 해킹 및 서버 장애가 감지되어 점검 중입니다. 정상적인 예약은 유선(02-1111-2222)으로 부탁드립니다."
    db.commit()
    print("Emergency mode activated!")

if __name__ == '__main__':
    print("Resetting emergency status to Normal...")
    reset_emergency()
    print("Waiting 10 seconds before simulating a hacker attack detection...")
    time.sleep(10)
    trigger_emergency()
    print("Done!")
