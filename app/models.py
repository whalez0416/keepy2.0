from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .db import Base
from .utils.crypto import EncryptedString

class UserRole(enum.Enum):
    SUPERADMIN = "superadmin"
    USER = "user"

class MembershipRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    org_memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False) # URL용 (예: min-hospital)
    logo_url = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)
    # 장애/변조 알림 수신처 (쉼표로 여러 명). 이메일은 즉시 발송, 휴대폰은 SMS/알림톡 연동 시 사용.
    notify_emails = Column(Text, nullable=True)
    notify_phones = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Billing & Subscription
    plan = Column(String, default="starter") # starter, pro, enterprise
    subscription_status = Column(String, default="active") # active, past_due, canceled
    subscription_period_end = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    sites = relationship("Site", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")

class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    org_id = Column(Integer, ForeignKey("organizations.id"))
    role = Column(Enum(MembershipRole), default=MembershipRole.VIEWER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="org_memberships")
    organization = relationship("Organization", back_populates="members")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    site_name = Column(String, nullable=False)
    hospital_name = Column(String, nullable=True) # 지점 구분용 (예: 강남점, 신촌점)
    homepage_url = Column(String, nullable=False)
    check_interval_minutes = Column(Integer, default=5)
    extra_steps_json = Column(Text, nullable=True)
    baseline_screenshot_path = Column(String, nullable=True) # (구) 파일경로 기반 기준 이미지 — 휘발성 디스크라 사용 중단
    # 시각적 변조 탐지용 기준 이미지를 DB에 직접 저장(PNG 바이트).
    # Render 디스크는 재배포 시 사라지므로, 파일이 아니라 DB에 보관해야 기준이 유지된다.
    baseline_screenshot_data = Column(LargeBinary, nullable=True)
    emergency_mode_active = Column(Boolean, default=False) # 긴급 안내 배너 활성화 여부
    emergency_message = Column(String, nullable=True) # 긴급 안내 메시지
    admin_path = Column(String, default="/admin") # 관리자 페이지 경로
    whitelisted_ips = Column(Text, nullable=True) # 허용된 IP 목록 (쉼표 구분)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="sites")
    form_configs = relationship("FormConfig", back_populates="site", cascade="all, delete-orphan")
    spam_configs = relationship("SpamConfig", back_populates="site")
    contact_configs = relationship("ContactConfig", back_populates="site", cascade="all, delete-orphan")

class FormConfig(Base):
    __tablename__ = "form_configs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    name = Column(String, nullable=False) # 폼 이름 (예: 메인 상담, 예약 폼)
    form_url = Column(String, nullable=False)
    check_interval_minutes = Column(Integer, default=60)
    expected_success_text = Column(String, nullable=True)
    # 실제 제출 여부. 기본 False = 제출하지 않고 폼이 살아있는지만 점검(고객 게시판 오염 방지).
    # True = 실제로 제출(전용 테스트 게시판 등 고객이 동의한 경우에만 권장).
    submit_test = Column(Boolean, default=False)
    
    # Form Selectors
    name_selector = Column(String, nullable=True)
    phone_selector = Column(String, nullable=True)
    subject_selector = Column(String, nullable=True)
    message_selector = Column(String, nullable=True)
    password_selector = Column(String, nullable=True)
    password_value = Column(EncryptedString, nullable=True)  # 폼 테스트용 비밀번호 — 암호화 저장
    agreement_selector = Column(String, nullable=True)
    submit_selector = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="form_configs")

class SpamConfig(Base):
    __tablename__ = "spam_configs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    board_url = Column(String, nullable=False)
    admin_id = Column(String, nullable=True)
    admin_pw = Column(EncryptedString, nullable=True)  # 고객 게시판 관리자 비밀번호 — 암호화 저장
    keywords = Column(Text, nullable=True) # 콤마로 구분된 금지어
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="spam_configs")

class ContactConfig(Base):
    __tablename__ = "contact_configs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    
    # Expected values
    expected_phone = Column(String, nullable=True)
    expected_kakao_url = Column(String, nullable=True)
    
    # Custom Selectors (optional, if defaults don't work)
    phone_selector = Column(String, nullable=True) 
    kakao_selector = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="contact_configs")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    check_type = Column(String)  # homepage, form
    status = Column(String)      # success, warning, fail
    response_time = Column(Float, nullable=True)
    fail_reason = Column(Text, nullable=True)
    raw_result = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    check_type = Column(String)
    alert_level = Column(String)  # warning, danger
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # 시스템 작업일 경우 null
    action = Column(String, nullable=False) # 예: CREATE_SITE, UPDATE_FORM, LOGIN
    target_type = Column(String) # Site, FormConfig, User 등
    target_id = Column(Integer)
    details = Column(Text, nullable=True) # JSON 또는 설명
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="audit_logs")

class LeadStatus(enum.Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    CONTACTED = "contacted"
    CLOSED = "closed"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    hospital_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=False)
    website_url = Column(String, nullable=False)
    plan = Column(String, nullable=True)
    inquiry = Column(Text, nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
