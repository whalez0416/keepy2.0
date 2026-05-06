from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["billing"])

@router.get("/status/{org_id}")
def get_billing_status(org_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 권한 확인
    membership = db.query(models.OrganizationMember).filter(
        models.OrganizationMember.user_id == current_user.id,
        models.OrganizationMember.org_id == org_id
    ).first()
    
    if not membership and current_user.role != models.UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="조직을 찾을 수 없습니다.")
        
    return {
        "plan": org.plan,
        "status": org.subscription_status,
        "period_end": org.subscription_period_end,
        "is_premium": org.plan in ["pro", "enterprise"]
    }

@router.post("/subscribe/{org_id}")
def subscribe_to_plan(org_id: int, plan: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 권한 확인 (Owner 또는 Superadmin 가능)
    is_superadmin = current_user.role.value == "superadmin"
    membership = db.query(models.OrganizationMember).filter(
        models.OrganizationMember.user_id == current_user.id,
        models.OrganizationMember.org_id == org_id
    ).first()
    
    is_owner = membership and membership.role.value == "owner"
    
    if not is_superadmin and not is_owner:
        raise HTTPException(status_code=403, detail="결제 권한이 없습니다. (조직 소유자만 가능)")
        
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="조직을 찾을 수 없습니다.")
        
    # 시뮬레이션: 결제 성공 처리
    org.plan = plan
    org.subscription_status = "active"
    org.subscription_period_end = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    return {"status": "success", "plan": plan, "expires_at": org.subscription_period_end}
