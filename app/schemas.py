from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class SiteBase(BaseModel):
    site_name: str
    hospital_name: Optional[str] = None
    homepage_url: str
    check_interval_minutes: int = 5
    extra_steps_json: Optional[str] = None
    is_active: bool = True

class FormConfigBase(BaseModel):
    name: str
    form_url: str
    check_interval_minutes: int = 60
    expected_success_text: Optional[str] = None
    name_selector: Optional[str] = None
    phone_selector: Optional[str] = None
    subject_selector: Optional[str] = None
    message_selector: Optional[str] = None
    password_selector: Optional[str] = None
    password_value: Optional[str] = None
    agreement_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    is_active: bool = True

class FormConfigCreate(FormConfigBase):
    pass

class FormConfig(FormConfigBase):
    id: int
    site_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SpamConfigBase(BaseModel):
    site_id: Optional[int] = None # Optional during creation if added within Site
    board_url: str
    admin_id: Optional[str] = None
    admin_pw: Optional[str] = None
    keywords: Optional[str] = None
    is_active: bool = True

class SpamConfig(SpamConfigBase):
    id: int
    site_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SiteCreate(SiteBase):
    form_configs: Optional[List[FormConfigCreate]] = []
    spam_configs: Optional[List[SpamConfigBase]] = []

class SiteUpdate(BaseModel):
    site_name: Optional[str] = None
    homepage_url: Optional[str] = None
    check_interval_minutes: Optional[int] = None
    extra_steps_json: Optional[str] = None
    is_active: Optional[bool] = None
    form_configs: Optional[List[FormConfigCreate]] = None
    spam_configs: Optional[List[SpamConfigBase]] = None

class Site(SiteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    form_configs: List[FormConfig] = []
    spam_configs: List[SpamConfig] = []

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

# New schemas for Multi-Tenancy
class UserBase(BaseModel):
    email: str
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MembershipBase(BaseModel):
    user_id: int
    site_id: int
    role: str

class Membership(MembershipBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
