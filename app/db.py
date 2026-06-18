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

    # (table, column, DDL 타입) — nullable 컬럼만 추가하므로 기존 행에 안전
    pending = [
        ("organizations", "notify_emails", "TEXT"),
        ("organizations", "notify_phones", "TEXT"),
    ]

    inspector = inspect(engine)
    with engine.begin() as conn:
        for table, column, coltype in pending:
            try:
                existing_cols = {c["name"] for c in inspector.get_columns(table)}
            except Exception:
                # 테이블 자체가 아직 없으면 create_all이 처리하므로 건너뜀
                continue
            if column not in existing_cols:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {coltype}'))
