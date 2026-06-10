from app.db import SessionLocal
from app.models import Site, Organization

def install():
    db = SessionLocal()
    try:
        # 1. 'Master Org' 조직 확인 (없으면 생성)
        org = db.query(Organization).filter(Organization.name == "Master Org").first()
        if not org:
            org = Organization(name="Master Org", slug="master-org")
            db.add(org)
            db.flush()
        
        # 2. 'Keepy 공식 홍보관' 사이트 확인 및 생성
        homepage = "http://localhost:8000/static/keepy_landing.html"
        site = db.query(Site).filter(Site.homepage_url == homepage).first()
        
        if not site:
            site = Site(
                org_id=org.id,
                site_name="Keepy 공식 홍보관",
                hospital_name="Keepy 본사",
                homepage_url=homepage,
                is_active=True,
                emergency_mode_active=False,
                emergency_message="🚨 [긴급 공지] Keepy 공식 홍보관 시스템 긴급 서버 점검 중입니다. 서비스 이용에 참고 바랍니다."
            )
            db.add(site)
            db.flush()
            db.commit()
            print(f"Registered new site in DB: ID={site.id}, Name={site.site_name}")
        else:
            print(f"Site already exists in DB: ID={site.id}, Name={site.site_name}")
            
        site_id = site.id
        
        # 3. 'app/static/keepy_landing.html'의 script 태그 업데이트
        landing_path = "app/static/keepy_landing.html"
        with open(landing_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 기존 주입 스크립트를 실제 DB의 ID로 치환
        old_script = '<script src="/static/keepy-banner.js" data-site-id="100"></script>'
        new_script = f'<script src="/static/keepy-banner.js" data-site-id="{site_id}"></script>'
        
        if old_script in content:
            content = content.replace(old_script, new_script)
            with open(landing_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Successfully updated {landing_path} with data-site-id='{site_id}'")
        else:
            # 혹시 다른 ID가 박혀있거나 하면 치환되지 않았을 수 있으니 검사
            import re
            pattern = r'<script src="/static/keepy-banner\.js" data-site-id="\d+"></script>'
            if re.search(pattern, content):
                content = re.sub(pattern, new_script, content)
                with open(landing_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Successfully updated script tag with data-site-id='{site_id}' via regex.")
            else:
                print("Could not find banner script tag in HTML to replace!")
                
    except Exception as e:
        print(f"Error during installation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    install()
