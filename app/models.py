from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from .db import Base

class UserRole(enum.Enum):
    SUPERADMIN = "superadmin"
    USER = "user"

class MembershipRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    memberships = relationship("Membership", back_populates="user")

class Membership(Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    site_id = Column(Integer, ForeignKey("sites.id"))
    role = Column(Enum(MembershipRole), default=MembershipRole.MEMBER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="memberships")
    site = relationship("Site", back_populates="memberships")


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String, nullable=False)
    hospital_name = Column(String, nullable=True) # 병원 그룹화용
    homepage_url = Column(String, nullable=False)
    form_url = Column(String, nullable=True)
    check_interval_minutes = Column(Integer, default=5)
    form_check_interval_minutes = Column(Integer, default=60)
    expected_success_text = Column(String, nullable=True)
    
    # Form Selectors
    name_selector = Column(String, nullable=True)
    phone_selector = Column(String, nullable=True)
    subject_selector = Column(String, nullable=True)
    message_selector = Column(String, nullable=True)
    password_selector = Column(String, nullable=True)
    password_value = Column(String, nullable=True)
    agreement_selector = Column(String, nullable=True)
    submit_selector = Column(String, nullable=True)
    
    # Advanced Action Sequence (JSON string)
    extra_steps_json = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    memberships = relationship("Membership", back_populates="site")
    spam_configs = relationship("SpamConfig", back_populates="site")

class SpamConfig(Base):
    __tablename__ = "spam_configs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    board_url = Column(String, nullable=False)
    admin_id = Column(String, nullable=True)
    admin_pw = Column(String, nullable=True)
    keywords = Column(Text, nullable=True) # 콤마로 구분된 금지어
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="spam_configs")

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
