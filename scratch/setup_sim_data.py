import sys
import os

sys.path.append(os.getcwd())

from app.db import SessionLocal, engine, Base
from app.models import User, UserRole, Organization, OrganizationMember, MembershipRole, Site
from app.api.auth import get_password_hash

def setup_simulation_data():
    # 1. Create Tables
    print("테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 2. Create Superadmin
        master_email = "master@keepy.com"
        if not db.query(User).filter(User.email == master_email).first():
            master_user = User(
                email=master_email,
                hashed_password=get_password_hash("keepy1234"),
                role=UserRole.SUPERADMIN,
                full_name="키피 마스터"
            )
            db.add(master_user)
            print(f"마스터 계정 생성 완료: {master_email}")
        
        # 3. Create Organizations (Hospitals)
        orgs = [
            {"name": "민트 병원", "slug": "mint-hospital"},
            {"name": "블루 성형외과", "slug": "blue-plastic"}
        ]
        
        db_orgs = []
        for org_data in orgs:
            existing_org = db.query(Organization).filter(Organization.slug == org_data["slug"]).first()
            if not existing_org:
                new_org = Organization(name=org_data["name"], slug=org_data["slug"])
                db.add(new_org)
                db_orgs.append(new_org)
                print(f"조직 생성 완료: {org_data['name']}")
            else:
                db_orgs.append(existing_org)
        
        db.flush() # ID 확보
        
        # 4. Create Regular User for Mint Hospital
        user_email = "user@mint.com"
        if not db.query(User).filter(User.email == user_email).first():
            regular_user = User(
                email=user_email,
                hashed_password=get_password_hash("user1234"),
                role=UserRole.USER,
                full_name="민트 관리자"
            )
            db.add(regular_user)
            db.flush()
            
            # Link to Mint Hospital
            membership = OrganizationMember(
                user_id=regular_user.id,
                org_id=db_orgs[0].id,
                role=MembershipRole.OWNER
            )
            db.add(membership)
            print(f"일반 유저 계정 생성 및 조직 연결 완료: {user_email}")

        # 5. Create Sample Sites
        # Mint Hospital Site
        if not db.query(Site).filter(Site.site_name == "민트 병원 메인").first():
            mint_site = Site(
                org_id=db_orgs[0].id,
                site_name="민트 병원 메인",
                hospital_name="강남점",
                homepage_url="https://mint-hospital.com",
                is_active=True
            )
            db.add(mint_site)
            print("민트 병원 사이트 생성 완료")

        # Blue Plastic Site
        if not db.query(Site).filter(Site.site_name == "블루 성형외과 공식").first():
            blue_site = Site(
                org_id=db_orgs[1].id,
                site_name="블루 성형외과 공식",
                hospital_name="압구정본점",
                homepage_url="https://blue-ps.co.kr",
                is_active=True
            )
            db.add(blue_site)
            print("블루 성형외과 사이트 생성 완료")

        db.commit()
        print("\n시뮬레이션 데이터 준비 완료!")
        print("-" * 30)
        print("마스터: master@keepy.com / keepy1234")
        print("일반유저: user@mint.com / user1234")
        
    except Exception as e:
        print(f"데이터 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_simulation_data()
