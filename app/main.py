from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db import engine, Base, SessionLocal
from app.api import sites, logs, alerts, checks, spam, auth, organizations, billing, leads
from app.api.auth import get_password_hash
from app.models import User, UserRole
from app.ui import views
from app.scheduler import scheduler, start_scheduler
from app.services.scheduler_service import init_all_jobs
from app.utils.logger import get_logger

# 로그 관리를 위한 로거 초기화
logger = get_logger("main")

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Keepy MVP", description="병원 웹사이트 모니터링 시스템")

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["Auth API"])
app.include_router(sites.router, prefix="/api/sites", tags=["Sites API"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations API"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing API"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs API"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts API"])
app.include_router(checks.router, prefix="/api/checks", tags=["Checks API"])
app.include_router(spam.router, prefix="/api/spam", tags=["Spam AI API"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads API"])

# UI 라우터 등록 (루트 경로)
app.include_router(views.router, tags=["Admin UI"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Keepy API Server is running"}

@app.get("/api/test/trigger")
def trigger_emergency():
    from app.models import Site
    from app.db import SessionLocal
    db = SessionLocal()
    site = db.query(Site).filter(Site.id == 9).first()
    if site:
        site.emergency_mode_active = True
        site.emergency_message = "📢 [긴급 안내] 해킹 및 서버 장애가 감지되어 점검 중입니다. 정상적인 예약은 유선(02-1111-2222)으로 부탁드립니다."
        db.commit()
    db.close()
    return {"triggered": True}


@app.on_event("startup")
def startup_event():
    logger.debug("서버 시작 중...")
    # 스케줄러 시작
    start_scheduler()
    # 활성 상태인 사이트들의 작업 로드 및 등록
    init_all_jobs()
    
    # 마스터 계정 자동 생성 (없을 경우)
    db = SessionLocal()
    try:
        admin_email = "master@keepy.com"
        admin_pw = "keepy1234"
        existing = db.query(User).filter(User.email == admin_email).first()
        if not existing:
            hashed_pw = get_password_hash(admin_pw)
            new_user = User(
                email=admin_email,
                hashed_password=hashed_pw,
                role=UserRole.SUPERADMIN
            )
            db.add(new_user)
            db.commit()
            logger.info(f"마스터 계정이 자동으로 생성되었습니다: {admin_email}")
    except Exception as e:
        logger.error(f"마스터 계정 생성 중 오류: {e}")
    finally:
        db.close()

    logger.debug("서버가 시작되었으며 모든 작업이 초기화되었습니다.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.debug("서버 종료 중.")
