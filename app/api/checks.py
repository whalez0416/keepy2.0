from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..services.homepage_checker import check_homepage
from ..services.form_checker import check_form
from ..services.alert_service import handle_check_result
from .auth import get_current_user

router = APIRouter(tags=["checks"])

@router.post("/run/{site_id}")
def run_manual_check(site_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Site).filter(models.Site.id == site_id)
    if current_user.role != models.UserRole.SUPERADMIN:
        query = query.join(models.Organization).join(models.OrganizationMember).filter(models.OrganizationMember.user_id == current_user.id)
        
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")

    # Run homepage check
    h_log = check_homepage(db, site)
    if h_log:
        handle_check_result(db, site, "homepage", h_log.status, h_log.fail_reason)

    # Run form checks
    form_results = []
    for f_config in site.form_configs:
        f_log = check_form(db, f_config) 
        if f_log:
            handle_check_result(db, site, "form", f_log.status, f_log.fail_reason)
            form_results.append({"name": f_config.name, "status": f_log.status})

    # Run visual defacement check
    from ..services.visual_checker import check_visual_defacement
    v_log = check_visual_defacement(db, site)

    # Run contact hijack check
    from ..services.contact_checker import check_contact
    c_results = []
    for c_config in site.contact_configs:
        c_log = check_contact(db, c_config)
        if c_log:
            c_results.append({"id": c_config.id, "status": c_log.status})

    return {
        "homepage": h_log.status if h_log else "skipped",
        "forms": form_results,
        "visual": v_log.status if v_log else "skipped",
        "contacts": c_results
    }
