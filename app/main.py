import os
import socket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.db import engine, Base, SessionLocal, run_light_migrations
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
# 기존 DB에 새 컬럼이 없으면 추가 (Alembic 미사용 환경용 경량 마이그레이션)
run_light_migrations()

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
    # Render의 healthCheckPath가 가리키는 엔드포인트. 웹 프로세스가 떠 있는지만 본다.
    # (감시 스레드 상태로 502/503을 내면 재시작 루프 위험이 있어, 그 판정은 아래
    #  /api/health/monitoring으로 분리한다.)
    return {"status": "ok", "message": "Keepy API Server is running"}


# 감시(스케줄러)가 '실제로' 살아 동작 중인지 판정하는 엔드포인트.
# 감시 제품의 급소: 웹은 멀쩡한데 백그라운드 스케줄러 스레드만 죽으면, 단순 헬스체크는
# 계속 ok라서 아무도 감시 중단을 모른다. 이 엔드포인트를 외부 업타임 모니터(UptimeRobot
# 무료 등)에 걸어두면, 감시가 멈추는 순간 운영자가 메일/문자로 통보받는다.
# 최소 점검 주기(홈페이지 기본 5분)를 한참 넘겨도 새 로그가 없으면 '멈춤'으로 본다.
_MONITORING_STALE_MINUTES = 20

@app.get("/api/health/monitoring")
def monitoring_health():
    from datetime import datetime, timezone, timedelta
    from app.models import Site, Log

    scheduler_running = bool(getattr(scheduler, "running", False))

    db = SessionLocal()
    try:
        active_sites = db.query(Site).filter(Site.is_active == True).count()
        last_log = db.query(Log).order_by(Log.checked_at.desc()).first()
        last_check_at = last_log.checked_at if last_log else None
    finally:
        db.close()

    minutes_since = None
    stale = False
    if last_check_at is not None:
        # checked_at은 timezone=True라 Postgres에선 aware, SQLite에선 naive로 온다.
        lc = last_check_at
        if lc.tzinfo is not None:
            lc = lc.astimezone(timezone.utc).replace(tzinfo=None)
        minutes_since = (datetime.utcnow() - lc).total_seconds() / 60.0
        stale = minutes_since > _MONITORING_STALE_MINUTES

    # 감시 건강 판정:
    #  - 스케줄러가 안 돌면 무조건 비정상.
    #  - 감시할 활성 사이트가 있는데도 한참 동안 점검 로그가 없으면(=스레드 wedge) 비정상.
    #  - 활성 사이트가 0이면 점검할 게 없으니 정상(부팅 직후 포함).
    healthy = scheduler_running and not (active_sites > 0 and (last_check_at is None or stale))

    payload = {
        "status": "ok" if healthy else "unhealthy",
        "scheduler_running": scheduler_running,
        "active_sites": active_sites,
        "last_check_at": last_check_at.isoformat() if last_check_at else None,
        "minutes_since_last_check": round(minutes_since, 1) if minutes_since is not None else None,
        "stale_threshold_minutes": _MONITORING_STALE_MINUTES,
    }
    if not healthy:
        # 503 → 외부 업타임 모니터가 '다운'으로 감지해 운영자에게 통보하게 한다.
        return JSONResponse(status_code=503, content=payload)
    return payload


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
# ⚠️ 워커를 2개 이상으로 늘릴 때 주의: 사이트 생성/수정 API가 락 없는 워커에서 처리되면
# update_site_jobs가 그 워커의 (돌지 않는) 스케줄러에만 등록돼 재부팅 전까지 감시가 누락된다.
# 워커 확장 전에 잡 등록을 DB 기반 폴링이나 스케줄러 워커로의 전달 방식으로 바꿔야 한다.
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

    # 마스터(운영자) 계정 시드 — MASTER_EMAIL/MASTER_PASSWORD가 있을 때만.
    # 보안: 계정이 '없을 때 1회만' 생성한다. 이미 있으면 비밀번호를 건드리지 않는다
    # (앱에서 비번을 바꿔도 부팅 때마다 평문 env값으로 되돌아가던 문제 방지).
    # 권한이 SUPERADMIN이 아니면 그것만 보정한다.
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
            elif existing.role != UserRole.SUPERADMIN:
                # 비밀번호는 그대로 두고 권한만 보정
                existing.role = UserRole.SUPERADMIN
                db.commit()
                logger.info(f"마스터 계정 권한을 SUPERADMIN으로 보정했습니다: {settings.MASTER_EMAIL}")
        except Exception as e:
            logger.error(f"마스터 계정 시드 중 오류: {e}")
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
