from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime

class SiteBase(BaseModel):
    site_name: str
    hospital_name: Optional[str] = None
    homepage_url: str
    check_interval_minutes: int = 5
    extra_steps_json: Optional[str] = None
    baseline_screenshot_path: Optional[str] = None
    emergency_mode_active: bool = False
    emergency_message: Optional[str] = None
    admin_path: Optional[str] = "/admin"
    whitelisted_ips: Optional[str] = None
    expected_phone: Optional[str] = None
    expected_kakao_url: Optional[str] = None
    is_active: bool = True

class FormConfigBase(BaseModel):
    name: str
    form_url: str
    check_interval_minutes: int = 60
    expected_success_text: Optional[str] = None
    submit_test: bool = False  # True일 때만 실제 제출(기본은 게시판 오염 방지 위해 미제출 점검)
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
    # 보안: 폼 테스트용 비밀번호는 응답으로 절대 내보내지 않는다(쓰기 전용).
    # 저장 여부만 알 수 있도록 has_password로 노출한다.
    password_value: Optional[str] = Field(default=None, exclude=True)
    has_password: bool = False

    @staticmethod
    def _has_pw(v) -> bool:
        return bool(v)

    def model_post_init(self, __context) -> None:
        # ORM에서 읽은 password_value 유무를 has_password로 변환 후 원본은 직렬화 제외
        object.__setattr__(self, "has_password", bool(self.password_value))

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
    # 보안: 게시판 관리자 비밀번호는 응답으로 내보내지 않는다(쓰기 전용).
    admin_pw: Optional[str] = Field(default=None, exclude=True)
    has_admin_pw: bool = False

    def model_post_init(self, __context) -> None:
        object.__setattr__(self, "has_admin_pw", bool(self.admin_pw))

    class Config:
        from_attributes = True

class SiteCreate(SiteBase):
    org_id: Optional[int] = None
    form_configs: Optional[List[FormConfigCreate]] = []
    spam_configs: Optional[List[SpamConfigBase]] = []

class SiteUpdate(BaseModel):
    site_name: Optional[str] = None
    homepage_url: Optional[str] = None
    check_interval_minutes: Optional[int] = None
    extra_steps_json: Optional[str] = None
    is_active: Optional[bool] = None
    org_id: Optional[int] = None
    baseline_screenshot_path: Optional[str] = None
    emergency_mode_active: Optional[bool] = None
    emergency_message: Optional[str] = None
    admin_path: Optional[str] = None
    whitelisted_ips: Optional[str] = None
    expected_phone: Optional[str] = None
    expected_kakao_url: Optional[str] = None
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

class HospitalAdminCreate(BaseModel):
    email: str
    password: str
    hospital_name: str
    plan: Optional[str] = "starter"

class User(UserBase):
    id: int
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None
    billing_email: Optional[str] = None
    # 장애/변조 알림 수신처 (쉼표로 여러 명)
    notify_emails: Optional[str] = None
    notify_phones: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    billing_email: Optional[str] = None
    notify_emails: Optional[str] = None
    notify_phones: Optional[str] = None

class Organization(OrganizationBase):
    id: int
    is_active: bool
    created_at: datetime
    plan: str
    subscription_status: str
    subscription_period_end: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrganizationMemberBase(BaseModel):
    user_id: int
    org_id: int
    role: str

class OrganizationMember(OrganizationMemberBase):
    id: int
    joined_at: datetime
    # 유저 정보를 포함하면 순환 참조 문제가 생길 수 있으므로 주의
    # user: User 
    # organization: Organization

    class Config:
        from_attributes = True

class AuditLogBase(BaseModel):
    org_id: int
    user_id: Optional[int] = None
    action: str
    target_type: str
    target_id: int
    details: Optional[str] = None
    ip_address: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Removed Membership schema as it's replaced by OrganizationMember
