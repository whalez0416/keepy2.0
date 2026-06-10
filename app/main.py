import os
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.db import engine, Base, SessionLocal
from app.api import sites, logs, alerts, checks, spam, auth, organizations, leads, discovery
from app.api.auth import get_password_hash, verify_password
from app.models import User, UserRole
from app.scheduler import scheduler, start_scheduler
from app.services.scheduler_service import init_all_jobs
from app.utils.logger import get_logger

# 로그 관리를 위한 로거 초기화
logger = get_logger("main")

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Keepy MVP", description="병원 웹사이트 모니터링 시스템")

# CORS 설정: 기본은 전체 허용("*"), 운영에서는 CORS_ORIGINS로 프론트 도메인만 허용 권장.
# 인증은 localStorage의 Bearer 토큰으로 처리하므로 쿠키 자격증명(credentials)은 사용하지 않음.
_origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [
    o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# API 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["Auth API"])
app.include_router(sites.router, prefix="/api/sites", tags=["Sites API"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations API"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs API"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts API"])
app.include_router(checks.router, prefix="/api/checks", tags=["Checks API"])
app.include_router(spam.router, prefix="/api/spam", tags=["Spam AI API"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads API"])
app.include_router(discovery.router, prefix="/api/discovery", tags=["Discovery API"])

# NOTE: 레거시 Jinja2 관리자 UI(app/ui/views.py)는 인증이 없고 모든 테넌트 데이터를
# 노출하던 심각한 보안 구멍이자, 현재 스키마와 맞지 않는 죽은 코드였으므로 마운트 제거함.
# 실제 관리 화면은 React 프론트엔드(frontend/)가 담당함.

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Keepy API Server is running"}


# ─────────────────────────────────────────────────────────────
# 단일 도메인 서빙 구성
#   /         → 영업용 랜딩 페이지 (app/static/keepy_landing.html)
#   /app, /app/*  → React 관리자 앱 (frontend/dist, basename="/app")
#   /api/*    → REST API
# 프론트와 API가 같은 출처에서 동작하므로 CORS/라우팅 문제가 없다.
# 로컬 개발 시 dist가 없으면 Vite 개발 서버(npm run dev)를 사용한다.
# ─────────────────────────────────────────────────────────────
from fastapi import HTTPException

_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
_LANDING_FILE = os.path.join(os.path.dirname(__file__), "static", "keepy_landing.html")
_INDEX_FILE = os.path.join(_FRONTEND_DIST, "index.html")
_HAS_BUILD = os.path.isfile(_INDEX_FILE)

if _HAS_BUILD:
    _assets_dir = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    # React 앱: /app 및 그 하위 클라이언트 라우트(/app/dashboard 등)
    @app.get("/app")
    def serve_app_root():
        return FileResponse(_INDEX_FILE)

    @app.get("/app/{full_path:path}")
    def serve_app(full_path: str):
        # 빌드된 실제 파일(pwa 아이콘 등)이면 그 파일을, 아니면 SPA index.html
        candidate = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(_INDEX_FILE)


@app.get("/")
def serve_landing():
    # 메인 = 영업 랜딩 페이지. (없으면 앱으로 폴백)
    if os.path.isfile(_LANDING_FILE):
        return FileResponse(_LANDING_FILE)
    if _HAS_BUILD:
        return FileResponse(_INDEX_FILE)
    return {"status": "ok", "message": "Keepy API Server is running"}


@app.get("/{full_path:path}")
def serve_root_catchall(full_path: str):
    # /api, /static, /assets, /app 은 위에서 이미 처리됨 → 여기로 오면 안 됨
    if full_path.startswith(("api/", "static/", "assets/", "app")):
        raise HTTPException(status_code=404, detail="Not Found")
    # 루트의 PWA/파비콘 등 실제 파일은 빌드 폴더에서 제공
    if _HAS_BUILD:
        candidate = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
    # 그 외 알 수 없는 루트 경로는 랜딩으로
    if os.path.isfile(_LANDING_FILE):
        return FileResponse(_LANDING_FILE)
    raise HTTPException(status_code=404, detail="Not Found")


# 스케줄러 단일 프로세스 보장용 락 소켓 (gunicorn 워커가 여럿이어도 1개만 스케줄러 실행)
_scheduler_lock_socket = None


def _acquire_scheduler_lock() -> bool:
    """로컬 포트 바인딩으로 프로세스 간 락 획득. 성공한 워커만 스케줄러를 돌린다."""
    global _scheduler_lock_socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        s.bind(("127.0.0.1", 47650))
        _scheduler_lock_socket = s  # 프로세스 생존 동안 점유 유지
        return True
    except OSError:
        s.close()
        return False


@app.on_event("startup")
def startup_event():
    logger.info("서버 시작 중...")

    # 스케줄러는 여러 워커 중 단 하나의 프로세스에서만 실행 (중복 점검/중복 알림 방지)
    if _acquire_scheduler_lock():
        start_scheduler()
        init_all_jobs()
        logger.info("이 워커에서 스케줄러를 시작하고 모든 작업을 초기화했습니다.")
    else:
        logger.info("다른 워커가 이미 스케줄러를 실행 중입니다. 이 워커는 API만 처리합니다.")

    # 마스터(운영자) 계정을 .env 값과 동기화 — MASTER_EMAIL/MASTER_PASSWORD가 있을 때만.
    # 계정이 없으면 생성하고, 있으면 비밀번호/권한을 .env 기준으로 맞춘다(.env가 진실의 원천).
    if settings.MASTER_EMAIL and settings.MASTER_PASSWORD:
        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == settings.MASTER_EMAIL).first()
            if not existing:
                db.add(User(
                    email=settings.MASTER_EMAIL,
                    hashed_password=get_password_hash(settings.MASTER_PASSWORD),
                    role=UserRole.SUPERADMIN,
                ))
                db.commit()
                logger.info(f"마스터 계정이 생성되었습니다: {settings.MASTER_EMAIL}")
            else:
                changed = False
                if not verify_password(settings.MASTER_PASSWORD, existing.hashed_password):
                    existing.hashed_password = get_password_hash(settings.MASTER_PASSWORD)
                    changed = True
                if existing.role != UserRole.SUPERADMIN:
                    existing.role = UserRole.SUPERADMIN
                    changed = True
                if changed:
                    db.commit()
                    logger.info(f"마스터 계정을 .env 기준으로 동기화했습니다: {settings.MASTER_EMAIL}")
        except Exception as e:
            logger.error(f"마스터 계정 동기화 중 오류: {e}")
        finally:
            db.close()
    else:
        logger.warning(
            "MASTER_EMAIL/MASTER_PASSWORD 미설정 — 마스터 계정 자동 생성을 건너뜁니다. "
            "운영 시 .env에 지정하세요."
        )

    logger.info("서버 시작 완료.")


@app.on_event("shutdown")
def shutdown_event():
    if scheduler.running:
        scheduler.shutdown()
    logger.info("서버 종료 중.")
