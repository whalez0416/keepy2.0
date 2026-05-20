import sys
import os

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Site, Organization

DB_URL = "sqlite:///../keepy.db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def toggle_emergency():
    db = SessionLocal()
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Test Org", slug="test-org")
        db.add(org)
        db.commit()

    site = db.query(Site).filter(Site.id == 9).first()
    if not site:
        print("Creating Site ID 9...")
        db.execute(text(f"INSERT INTO sites (id, org_id, site_name, homepage_url, emergency_mode_active, emergency_message, is_active) VALUES (9, {org.id}, 'Mock Hospital', 'http://localhost:8000/static/mock_hospital.html', 1, '📢 [긴급] 홈페이지 에러가 감지되어 점검 중입니다. 진료 예약은 02-1111-2222로 연락 바랍니다.', 1)"))
        db.commit()
        print("Site 9 created and emergency mode ACTIVATED.")
    else:
        site.emergency_mode_active = not site.emergency_mode_active
        if site.emergency_mode_active:
            site.emergency_message = "📢 [긴급] 홈페이지 이상이 감지되어 서버를 보호하고 있습니다. 유선 예약(02-1111-2222) 부탁드립니다."
        db.commit()
        print(f"Site 9 emergency mode set to: {site.emergency_mode_active}")

if __name__ == '__main__':
    toggle_emergency()
