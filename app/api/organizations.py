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
