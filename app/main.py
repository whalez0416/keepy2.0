from fastapi import FastAPI
from .db import engine, Base
from .api import sites, logs, alerts, checks
from .scheduler import start_scheduler
from .services.scheduler_service import init_all_jobs
from .utils.logger import get_logger

# 로그 관리를 위한 로거 초기화
logger = get_logger("main")

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Keepy MVP", description="병원 웹사이트 모니터링 시스템")

# API 라우터 포함
app.include_router(sites.router)
app.include_router(logs.router)
app.include_router(alerts.router)
app.include_router(checks.router)

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
    from .scheduler import scheduler
    scheduler.shutdown()
    logger.debug("서버 종료 중.")

@app.get("/")
def root():
    return {"message": "Keepy MVP API에 오신 것을 환영합니다"}
