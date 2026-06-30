import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Keepy MVP"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # DB: SQLite(로컬) / PostgreSQL(운영) 모두 DATABASE_URL 하나로 동작.
    # 운영 전환 시 DATABASE_URL=postgresql://... 만 넣으면 코드 수정 불필요.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./keepy.db")

    # 보안: JWT 서명 키. 운영(DEBUG=False)에서 반드시 .env로 지정해야 함.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))  # 기본 24시간

    # B2B 수동 발급: 마스터(운영자) 계정. .env로 지정. 미지정 시 자동 생성 생략.
    MASTER_EMAIL: str = os.getenv("MASTER_EMAIL", "")
    MASTER_PASSWORD: str = os.getenv("MASTER_PASSWORD", "")

    # 공개 회원가입 허용 여부. B2B 수동 발급 모델이므로 기본 False(아무나 가입 못 함).
    # 마스터가 /api/auth/create-hospital-admin 로 고객 계정을 발급한다.
    ALLOW_PUBLIC_REGISTRATION: bool = os.getenv("ALLOW_PUBLIC_REGISTRATION", "False").lower() == "true"

    # CORS 허용 출처(쉼표 구분). 운영에서는 프론트 도메인으로 좁힐 것. 기본은 전체 허용.
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "no-reply@keepy.com")

    ALERT_COOLDOWN_HOURS: int = 1
    HOMEPAGE_FAIL_THRESHOLD: int = 2
    FORM_FAIL_THRESHOLD: int = 1

    # 스크린샷 보존 기간(일). 이 기간이 지난 점검 스크린샷은 매일 자동 삭제된다.
    # 보관이 필요한 스크린샷은 사용자가 로그 상세에서 다운로드해 따로 보관한다.
    SCREENSHOT_RETENTION_DAYS: int = int(os.getenv("SCREENSHOT_RETENTION_DAYS", "30"))

    # AI 스팸 분류 (OpenAI / GPT API)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# 운영(DEBUG=False)에서 DATABASE_URL을 깜빡하면 기본값(SQLite)로 조용히 떠서
# 재배포 때마다 모든 고객 데이터가 사라진다(Render 디스크는 휘발성). 그런 침묵 실패보다
# 부팅을 막아 즉시 알아채게 한다. (SECRET_KEY와 동일한 'loud failure' 정책)
if not settings.DEBUG and settings.DATABASE_URL.strip().lower().startswith("sqlite"):
    raise RuntimeError(
        "운영 환경(DEBUG=False)에서 DATABASE_URL이 SQLite입니다. "
        "Render/배포 환경변수에 관리형 PostgreSQL(postgresql://...) URL을 설정하세요. "
        "(SQLite는 재배포 시 데이터가 사라지므로 운영 사용 금지)"
    )
