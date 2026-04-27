import sys
import os

sys.path.append(os.getcwd())

from app.db import SessionLocal
from app.models import User, UserRole
from app.api.auth import get_password_hash

def create_superadmin():
    db = SessionLocal()
    email = "master@keepy.com"
    password = "keepy1234"
    
    try:
        # Check if already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"이미 {email} 계정이 존재합니다.")
            return

        hashed_pw = get_password_hash(password)
        new_user = User(
            email=email,
            hashed_password=hashed_pw,
            role=UserRole.SUPERADMIN
        )
        db.add(new_user)
        db.commit()
        print(f"마스터 계정이 생성되었습니다.")
        print(f"아이디: {email}")
        print(f"비밀번호: {password}")
    except Exception as e:
        print(f"계정 생성 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_superadmin()
