from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db import engine, Base
from app.api import sites, logs, alerts, checks
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
app.include_router(sites.router, prefix="/api/sites", tags=["Sites API"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs API"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts API"])
app.include_router(checks.router, prefix="/api/checks", tags=["Checks API"])

# UI 라우터 등록 (루트 경로)
app.include_router(views.router, tags=["Admin UI"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Keepy API Server is running"}

@app.on_event("startup")
def startup_event():
    logger.debug("서버 시작 중...")
    # 스케줄러 시작
    start_scheduler()
    # 활성 상태인 사이트들의 작업 로드 및 등록
    init_all_jobs()
    logger.debug("서버가 시작되었으며 모든 작업이 초기화되었습니다.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.debug("서버 종료 중.")
