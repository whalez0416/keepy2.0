from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, EmailStr
from app.db import get_db
from app.models import Lead, LeadStatus, User, UserRole
from app.api.auth import get_current_user
from app.services.slack_service import send_new_lead_notification
import traceback

router = APIRouter()

# Schema for incoming lead from the landing page
class LeadCreate(BaseModel):
    hospital_name: str
    contact_name: str
    phone_number: str
    email: EmailStr
    website_url: str
    plan: str
    inquiry: str = ""

# Schema for returning lead data
class LeadResponse(BaseModel):
    id: int
    hospital_name: str
    contact_name: str
    phone_number: str
    email: str
    website_url: str
    plan: str
    inquiry: str
    status: str
    created_at: str

    class Config:
        orm_mode = True

# Schema for updating lead status
class LeadUpdate(BaseModel):
    status: str

@router.post("/", status_code=201)
def create_lead(lead: LeadCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    랜딩페이지에서 폼 제출 시 호출되는 엔드포인트.
    DB에 저장하고 슬랙으로 알림을 보냅니다.
    """
    try:
        # DB 저장
        new_lead = Lead(
            hospital_name=lead.hospital_name,
            contact_name=lead.contact_name,
            phone_number=lead.phone_number,
            email=lead.email,
            website_url=lead.website_url,
            plan=lead.plan,
            inquiry=lead.inquiry
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)

        # 비동기로 슬랙 알림 전송 (응답 속도 향상을 위해)
        background_tasks.add_task(send_new_lead_notification, lead.dict())

        return {"status": "success", "message": "Lead captured successfully", "lead_id": new_lead.id}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to capture lead")


@router.get("/", response_model=List[LeadResponse])
def get_leads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    관리자 페이지에서 문의 목록을 불러오는 엔드포인트. (인증 필요, SUPERADMIN 전용)
    """
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to view leads")
        
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    # Pydantic 모델에 맞게 변환
    result = []
    for l in leads:
        result.append(LeadResponse(
            id=l.id,
            hospital_name=l.hospital_name,
            contact_name=l.contact_name,
            phone_number=l.phone_number,
            email=l.email,
            website_url=l.website_url,
            plan=l.plan or "",
            inquiry=l.inquiry or "",
            status=l.status.value,
            created_at=l.created_at.isoformat() if l.created_at else ""
        ))
    return result

@router.patch("/{lead_id}/status")
def update_lead_status(lead_id: int, update_data: LeadUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    문의 처리 상태 업데이트. (SUPERADMIN 전용)
    """
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update leads")
        
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    try:
        new_status = LeadStatus(update_data.status)
        lead.status = new_status
        db.commit()
        return {"status": "success", "new_status": new_status.value}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status value")
