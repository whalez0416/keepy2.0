from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from .db import Base

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String, nullable=False)
    homepage_url = Column(String, nullable=False)
    form_url = Column(String, nullable=True)
    check_interval_minutes = Column(Integer, default=5)
    form_check_interval_minutes = Column(Integer, default=60)
    expected_success_text = Column(String, nullable=True)
    
    # Form Selectors
    name_selector = Column(String, nullable=True)
    phone_selector = Column(String, nullable=True)
    message_selector = Column(String, nullable=True)
    submit_selector = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    check_type = Column(String)  # homepage, form
    status = Column(String)      # success, warning, fail
    response_time = Column(Float, nullable=True)
    fail_reason = Column(Text, nullable=True)
    raw_result = Column(Text, nullable=True)
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
