import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Keepy MVP"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Railway 등 클라우드 환경에서는 /data/keepy.db 경로를 선호함
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./keepy.db")
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@keepy.com"
    
    ALERT_COOLDOWN_HOURS: int = 1
    HOMEPAGE_FAIL_THRESHOLD: int = 2
    FORM_FAIL_THRESHOLD: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
