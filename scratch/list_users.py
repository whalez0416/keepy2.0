import sys
import os

sys.path.append(os.getcwd())

from app.db import SessionLocal
from app.models import User
from sqlalchemy import select

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            print("현재 등록된 사용자가 없습니다.")
        else:
            print("등록된 사용자 목록:")
            for user in users:
                print(f"- ID: {user.id}, Email: {user.email}, Role: {user.role}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
