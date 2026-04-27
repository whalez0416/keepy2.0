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
        query = query.join(models.Membership).filter(models.Membership.user_id == current_user.id)
        
    site = query.first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found or access denied")

    # Run homepage check
    h_log = check_homepage(db, site)
    if h_log:
        handle_check_result(db, site, "homepage", h_log.status, h_log.fail_reason)

    # Run form check
    f_log = None
    if site.form_url:
        f_log = check_form(db, site)
        if f_log:
            handle_check_result(db, site, "form", f_log.status, f_log.fail_reason)

    return {
        "homepage": h_log.status if h_log else "skipped",
        "form": f_log.status if f_log else "skipped"
    }
