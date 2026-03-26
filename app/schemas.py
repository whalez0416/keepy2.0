from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class SiteBase(BaseModel):
    site_name: str
    homepage_url: str
    form_url: Optional[str] = None
    check_interval_minutes: int = 5
    form_check_interval_minutes: int = 60
    expected_success_text: Optional[str] = None
    name_selector: Optional[str] = None
    phone_selector: Optional[str] = None
    message_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    is_active: bool = True

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    site_name: Optional[str] = None
    homepage_url: Optional[str] = None
    form_url: Optional[str] = None
    check_interval_minutes: Optional[int] = None
    form_check_interval_minutes: Optional[int] = None
    expected_success_text: Optional[str] = None
    name_selector: Optional[str] = None
    phone_selector: Optional[str] = None
    message_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    is_active: Optional[bool] = None

class Site(SiteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class LogBase(BaseModel):
    site_id: int
    check_type: str
    status: str
    response_time: Optional[float] = None
    fail_reason: Optional[str] = None
    raw_result: Optional[str] = None
    checked_at: datetime

class Log(LogBase):
    id: int

    class Config:
        from_attributes = True

class AlertBase(BaseModel):
    site_id: int
    check_type: str
    alert_level: str
    message: str
    sent_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

class Alert(AlertBase):
    id: int

    class Config:
        from_attributes = True
