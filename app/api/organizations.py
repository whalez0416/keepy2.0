from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from .. import models, schemas
from .auth import get_current_user

router = APIRouter(tags=["organizations"])

@router.get("/", response_model=List[schemas.Organization])
def list_organizations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    조직(병원 그룹) 목록을 조회합니다.
    - Superadmin: 모든 조직 조회 가능
    - User: 자신이 소속된 조직만 조회 가능
    """
    if current_user.role == models.UserRole.SUPERADMIN:
        return db.query(models.Organization).all()
    
    # 사용자가 속한 조직들 조회
    return db.query(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id).all()

@router.post("/", response_model=schemas.Organization)
def create_organization(org: schemas.OrganizationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    새로운 조직을 생성합니다. (Superadmin 전용)
    """
    if current_user.role != models.UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="조직 생성 권한이 없습니다.")
    
    db_org = models.Organization(**org.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

@router.patch("/{org_id}", response_model=schemas.Organization)
def update_organization(org_id: int, payload: schemas.OrganizationUpdate,
                        db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    """조직 정보(알림 수신 이메일/휴대폰 등)를 수정합니다.

    권한: Superadmin 또는 해당 조직의 OWNER/ADMIN 멤버.
    """
    org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if current_user.role != models.UserRole.SUPERADMIN:
        membership = db.query(models.OrganizationMember).filter(
            models.OrganizationMember.org_id == org_id,
            models.OrganizationMember.user_id == current_user.id,
        ).first()
        if not membership or membership.role not in (
            models.MembershipRole.OWNER, models.MembershipRole.ADMIN
        ):
            raise HTTPException(status_code=403, detail="조직 수정 권한이 없습니다.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, field, value)

    db.commit()
    db.refresh(org)
    return org

@router.get("/{org_id}", response_model=schemas.Organization)
def get_organization(org_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    특정 조직의 상세 정보를 조회합니다.
    """
    query = db.query(models.Organization).filter(models.Organization.id == org_id)
    
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)
        
    org = query.first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found or access denied")
    return org
