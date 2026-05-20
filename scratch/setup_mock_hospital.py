import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DB_URL = "sqlite:///./keepy.db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def setup_mock_hospital():
    print("[INIT] Setting up Gangnam Eye Clinic (강남아이안과) in Database...")
    db = SessionLocal()
    
    # 1. Clean up existing '강남아이안과' entries if any
    try:
        # Get existing site id first to clean up children
        res = db.execute(text("SELECT id FROM sites WHERE site_name='강남아이안과'")).fetchone()
        if res:
            site_id = res[0]
            print(f"[CLEANUP] Found existing site with ID {site_id}. Deleting dependencies...")
            db.execute(text(f"DELETE FROM alerts WHERE site_id={site_id}"))
            db.execute(text(f"DELETE FROM logs WHERE site_id={site_id}"))
            db.execute(text(f"DELETE FROM form_configs WHERE site_id={site_id}"))
            db.execute(text(f"DELETE FROM contact_configs WHERE site_id={site_id}"))
            db.execute(text(f"DELETE FROM sites WHERE id={site_id}"))
            db.commit()
    except Exception as e:
        print(f"[CLEANUP] Error cleaning up: {e}")
        db.rollback()

    # 2. Register Site
    try:
        # We assign org_id = 10 (Master Org) or 1 as fallback
        org_res = db.execute(text("SELECT id FROM organizations WHERE slug='master-org'")).fetchone()
        org_id = org_res[0] if org_res else 10
        
        print(f"[REGISTER] Inserting site with org_id={org_id}...")
        
        # Insert site explicitly with ID 9 (or auto-increment, but let's do auto-increment and retrieve the id)
        # Note: We keep ID 9 in the html script tag, so let's try to explicitly force ID 9 if possible, or update the HTML after.
        # But SQLite handles explicit ID insertion fine if it doesn't conflict!
        
        # Check if ID 9 is occupied by another site
        id_conflict = db.execute(text("SELECT site_name FROM sites WHERE id=9")).fetchone()
        if id_conflict:
            print(f"[WARNING] Site ID 9 is occupied by '{id_conflict[0]}'. Deleting conflict...")
            db.execute(text("DELETE FROM form_configs WHERE site_id=9"))
            db.execute(text("DELETE FROM contact_configs WHERE site_id=9"))
            db.execute(text("DELETE FROM logs WHERE site_id=9"))
            db.execute(text("DELETE FROM alerts WHERE site_id=9"))
            db.execute(text("DELETE FROM sites WHERE id=9"))
            db.commit()
            
        insert_site_query = text("""
            INSERT INTO sites (id, org_id, site_name, hospital_name, homepage_url, check_interval_minutes, 
                              emergency_mode_active, emergency_message, admin_path, is_active)
            VALUES (9, :org_id, '강남아이안과', '강남점', 'http://127.0.0.1:8000/static/mock_hospital.html', 5,
                    0, '현재 시스템 임시 서버 점검 중입니다. 급한 용무는 고객센터로 연락 바랍니다.', '/admin-panel', 1)
        """)
        
        db.execute(insert_site_query, {"org_id": org_id})
        db.commit()
        print("[SUCCESS] Site '강남아이안과' inserted with ID 9.")
        
        # 3. Insert Form Config
        insert_form_query = text("""
            INSERT INTO form_configs (site_id, name, form_url, check_interval_minutes, expected_success_text,
                                     name_selector, phone_selector, subject_selector, message_selector,
                                     agreement_selector, submit_selector, is_active)
            VALUES (9, '빠른 온라인 상담', 'http://127.0.0.1:8000/static/mock_hospital.html', 60, 
                    '상담 예약이 성공적으로 접수되었습니다', '#name-input', '#phone-input', '#subject-input',
                    '#message-input', '#agree-checkbox', '#submit-btn', 1)
        """)
        db.execute(insert_form_query)
        
        # 4. Insert Contact Config
        insert_contact_query = text("""
            INSERT INTO contact_configs (site_id, expected_phone, expected_kakao_url, phone_selector, kakao_selector, is_active)
            VALUES (9, '02-1111-2222', 'https://pf.kakao.com/original', '#phone-link', '#kakao-link', 1)
        """)
        db.execute(insert_contact_query)
        
        db.commit()
        print("[SUCCESS] FormConfig and ContactConfig inserted successfully.")
        
    except Exception as e:
        print(f"[FATAL] Failed to insert site configuration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_mock_hospital()
