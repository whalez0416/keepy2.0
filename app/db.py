from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# SQLite는 멀티스레드 사용을 위해 check_same_thread=False 필요.
# PostgreSQL 등 다른 DB에서는 해당 옵션을 주면 에러가 나므로 분기 처리.
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # 끊긴 커넥션 자동 감지(운영 DB 안정성)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_light_migrations():
    """경량 컬럼 마이그레이션.

    Alembic 없이 운영하므로, 모델에 새로 추가된 컬럼이 기존 테이블에 없으면
    ADD COLUMN으로 채운다. SQLite/Postgres 모두에서 안전하게 동작한다.
    (신규 배포 Postgres는 create_all로 이미 생성되므로 사실상 no-op)
    """
    from sqlalchemy import inspect, text

    # 바이너리 컬럼 타입은 DB마다 다르다: Postgres=BYTEA, SQLite=BLOB.
    _binary_type = "BLOB" if settings.DATABASE_URL.startswith("sqlite") else "BYTEA"

    # (table, column, DDL 타입) — nullable/기본값 컬럼만 추가하므로 기존 행에 안전.
    # 기본값은 SQLite/Postgres 모두에서 유효한 표현만 사용(boolean은 false).
    pending = [
        ("organizations", "notify_emails", "TEXT"),
        ("organizations", "notify_phones", "TEXT"),
        ("form_configs", "submit_test", "BOOLEAN DEFAULT false"),
        ("sites", "baseline_screenshot_data", _binary_type),
    ]

    inspector = inspect(engine)
    for table, column, coltype in pending:
        try:
            existing_cols = {c["name"] for c in inspector.get_columns(table)}
        except Exception:
            # 테이블 자체가 아직 없으면 create_all이 처리하므로 건너뜀
            continue
        if column in existing_cols:
            continue
        # 각 ALTER를 독립 트랜잭션 + try/except로 감싼다: 동시 부팅(여러 워커)에서
        # 한 워커가 먼저 추가해 'duplicate column'이 나도 부팅이 죽지 않도록.
        try:
            with engine.begin() as conn:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {coltype}'))
        except Exception as e:
            # 이미 다른 워커가 추가했거나 경합 — 무시(다음 부팅엔 존재 체크에서 걸러짐)
            from .utils.logger import get_logger
            get_logger("db").debug(f"마이그레이션 ADD COLUMN {table}.{column} 건너뜀: {e}")
