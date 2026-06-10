from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
import os

from ..db import get_db
from ..config import settings
from .. import models, schemas

# SECURITY CONFIG
# JWT 서명 키는 반드시 환경변수(.env)로 주입. 운영(DEBUG=False)에서 미설정 시 부팅 실패시킴.
SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    if settings.DEBUG:
        # 개발 환경 편의를 위한 임시 키 (운영에서는 절대 사용 안 됨)
        SECRET_KEY = "dev-only-insecure-key-change-me"
    else:
        raise RuntimeError(
            "SECRET_KEY 환경변수가 설정되지 않았습니다. 운영 환경에서는 .env 또는 "
            "배포 설정에 SECRET_KEY(길고 랜덤한 문자열)를 반드시 지정해야 합니다."
        )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

router = APIRouter(tags=["auth"])

class Token(BaseModel):
    access_token: str
    token_type: str
    user: schemas.User

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 마지막 로그인 시간 기록
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    hashed_pw = get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pw,
        role=models.UserRole.USER
    )
    db.add(new_user)
    db.flush() # ID를 얻기 위해 flush
    
    # 기본 조직 생성 (유저 이메일을 기반으로 슬러그 생성)
    org_name = f"{user.email.split('@')[0]}'s Workspace"
    org_slug = user.email.split('@')[0].replace('.', '-')
    
    # 슬러그 중복 방지 (간단하게)
    existing_org = db.query(models.Organization).filter(models.Organization.slug == org_slug).first()
    if existing_org:
        org_slug = f"{org_slug}-{new_user.id}"
        
    new_org = models.Organization(
        name=org_name,
        slug=org_slug,
        billing_email=user.email
    )
    db.add(new_org)
    db.flush()
    
    # 유저를 조직의 OWNER로 등록
    new_membership = models.OrganizationMember(
        user_id=new_user.id,
        org_id=new_org.id,
        role=models.MembershipRole.OWNER
    )
    db.add(new_membership)
    
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """로그인한 사용자가 자신의 비밀번호를 변경한다."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="새 비밀번호는 8자 이상이어야 합니다.")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="새 비밀번호가 기존과 동일합니다.")

    current_user.hashed_password = get_password_hash(body.new_password)
    db.commit()

    # 참고: 마스터(.env로 관리되는) 계정은 서버 재시작 시 .env 값으로 되돌아갈 수 있음.
    return {"status": "ok", "message": "비밀번호가 변경되었습니다."}

@router.post("/create-hospital-admin", response_model=schemas.User)
def create_hospital_admin(
    admin_data: schemas.HospitalAdminCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 권한 검사
    if current_user.role != models.UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="권한이 없습니다. 마스터 관리자만 이용할 수 있습니다.")

    db_user = db.query(models.User).filter(models.User.email == admin_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    # 1. 유저 계정 생성
    hashed_pw = get_password_hash(admin_data.password)
    new_user = models.User(
        email=admin_data.email,
        hashed_password=hashed_pw,
        role=models.UserRole.USER
    )
    db.add(new_user)
    db.flush()

    # 2. 조직(병원 그룹) 생성
    org_slug = admin_data.hospital_name.lower().replace(" ", "-").replace(".", "-")
    existing_org = db.query(models.Organization).filter(models.Organization.slug == org_slug).first()
    if existing_org:
        org_slug = f"{org_slug}-{new_user.id}"

    new_org = models.Organization(
        name=admin_data.hospital_name,
        slug=org_slug,
        billing_email=admin_data.email,
        plan=admin_data.plan or "starter",
        subscription_status="active"
    )
    db.add(new_org)
    db.flush()

    # 3. 유저를 해당 조직의 OWNER로 연동
    new_membership = models.OrganizationMember(
        user_id=new_user.id,
        org_id=new_org.id,
        role=models.MembershipRole.OWNER
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_user)

    return new_user
