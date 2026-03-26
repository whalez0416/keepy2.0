import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Keepy MVP"
    DEBUG: bool = True
    
    DATABASE_URL: str = "sqlite:///./keepy.db"
    
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
