import sys
import os

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Site, Organization
from app.db import SessionLocal
from sqlalchemy import text

def toggle_landing_emergency():
    db = SessionLocal()
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="Keepy HQ", slug="keepy-hq")
        db.add(org)
        db.commit()

    site = db.query(Site).filter(Site.id == 100).first()
    if not site:
        print("Creating Site ID 100 for Keepy Landing Page...")
        db.execute(text(f"INSERT INTO sites (id, org_id, site_name, homepage_url, emergency_mode_active, emergency_message, is_active) VALUES (100, {org.id}, 'Keepy Landing Page', 'http://localhost:8000/static/keepy_landing.html', 1, '📢 [긴급] 홈페이지 점검 중입니다. 서비스 도입 및 문의는 02-999-9999 로 부탁드립니다.', 1)"))
        db.commit()
        print("Site 100 created and emergency mode ACTIVATED.")
    else:
        site.emergency_mode_active = not site.emergency_mode_active
        db.commit()
        print(f"Site 100 emergency mode set to: {site.emergency_mode_active}")

if __name__ == '__main__':
    toggle_landing_emergency()
