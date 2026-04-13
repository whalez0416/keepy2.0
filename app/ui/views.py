from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas
from app.services.status_service import get_site_summary
from app.services.scheduler_service import update_site_jobs, remove_site_jobs, run_site_check
from app.utils.logger import logger

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    logger.debug("[DEBUG] render dashboard")
    sites = db.query(models.Site).all()
    summaries = [get_site_summary(db, site) for site in sites]
    return templates.TemplateResponse(
        request=request, name="dashboard.html", context={"sites": summaries}
    )

@router.get("/sites/new", response_class=HTMLResponse)
def new_site_form(request: Request):
    logger.debug("[DEBUG] render site form (new)")
    return templates.TemplateResponse(
        request=request, name="site_form.html", context={"site": None}
    )

@router.post("/sites/new")
def create_site_ui(
    site_name: str = Form(...),
    homepage_url: str = Form(...),
    form_url: str = Form(None),
    check_interval_minutes: int = Form(5),
    form_check_interval_minutes: int = Form(60),
    expected_success_text: str = Form(None),
    name_selector: str = Form(None),
    phone_selector: str = Form(None),
    subject_selector: str = Form(None),
    message_selector: str = Form(None),
    password_selector: str = Form(None),
    password_value: str = Form(None),
    agreement_selector: str = Form(None),
    submit_selector: str = Form(None),
    extra_steps_json: str = Form(None),
    is_active: bool = Form(True),
    db: Session = Depends(get_db)
):
    db_site = models.Site(
        site_name=site_name,
        homepage_url=homepage_url,
        form_url=form_url,
        check_interval_minutes=check_interval_minutes,
        form_check_interval_minutes=form_check_interval_minutes,
        expected_success_text=expected_success_text,
        name_selector=name_selector,
        phone_selector=phone_selector,
        subject_selector=subject_selector,
        message_selector=message_selector,
        password_selector=password_selector,
        password_value=password_value,
        agreement_selector=agreement_selector,
        submit_selector=submit_selector,
        extra_steps_json=extra_steps_json,
        is_active=is_active
    )
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    update_site_jobs(db_site)
    logger.debug(f"[DEBUG] site created from UI: site_id={db_site.id}")
    return RedirectResponse(url="/", status_code=303)

@router.get("/sites/{site_id}/edit", response_class=HTMLResponse)
def edit_site_form(site_id: int, request: Request, db: Session = Depends(get_db)):
    logger.debug(f"[DEBUG] render site form (edit): site_id={site_id}")
    site = db.query(models.Site).get(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return templates.TemplateResponse(
        request=request, name="site_form.html", context={"site": site}
    )

@router.post("/sites/{site_id}/edit")
def update_site_ui(
    site_id: int,
    site_name: str = Form(...),
    homepage_url: str = Form(...),
    form_url: str = Form(None),
    check_interval_minutes: int = Form(...),
    form_check_interval_minutes: int = Form(...),
    expected_success_text: str = Form(None),
    name_selector: str = Form(None),
    phone_selector: str = Form(None),
    subject_selector: str = Form(None),
    message_selector: str = Form(None),
    password_selector: str = Form(None),
    password_value: str = Form(None),
    agreement_selector: str = Form(None),
    submit_selector: str = Form(None),
    extra_steps_json: str = Form(None),
    is_active: bool = Form(False),
    db: Session = Depends(get_db)
):
    db_site = db.query(models.Site).get(site_id)
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    db_site.site_name = site_name
    db_site.homepage_url = homepage_url
    db_site.form_url = form_url
    db_site.check_interval_minutes = check_interval_minutes
    db_site.form_check_interval_minutes = form_check_interval_minutes
    db_site.expected_success_text = expected_success_text
    db_site.name_selector = name_selector
    db_site.phone_selector = phone_selector
    db_site.subject_selector = subject_selector
    db_site.message_selector = message_selector
    db_site.password_selector = password_selector
    db_site.password_value = password_value
    db_site.agreement_selector = agreement_selector
    db_site.submit_selector = submit_selector
    db_site.extra_steps_json = extra_steps_json
    db_site.is_active = is_active
    
    db.commit()
    update_site_jobs(db_site)
    logger.debug(f"[DEBUG] site updated from UI: site_id={site_id}")
    return RedirectResponse(url="/", status_code=303)

@router.post("/sites/{site_id}/toggle")
def toggle_site(site_id: int, db: Session = Depends(get_db)):
    db_site = db.query(models.Site).get(site_id)
    if db_site:
        db_site.is_active = not db_site.is_active
        db.commit()
        if db_site.is_active:
            update_site_jobs(db_site)
        else:
            remove_site_jobs(site_id)
        logger.debug(f"[DEBUG] site toggle from UI: site_id={site_id}, active={db_site.is_active}")
    return RedirectResponse(url="/", status_code=303)

@router.post("/sites/{site_id}/check")
def manual_check_ui(site_id: int):
    logger.debug(f"[DEBUG] manual check triggered from UI: site_id={site_id}")
    # Run homepage and form check manually
    run_site_check(site_id, "homepage")
    run_site_check(site_id, "form")
    return RedirectResponse(url="/", status_code=303)

@router.get("/logs", response_class=HTMLResponse)
def logs_page(request: Request, db: Session = Depends(get_db)):
    logger.debug("[DEBUG] render logs page")
    logs = db.query(models.Log).order_by(models.Log.created_at.desc()).limit(100).all()
    return templates.TemplateResponse(
        request=request, name="logs.html", context={"logs": logs}
    )

@router.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request, db: Session = Depends(get_db)):
    logger.debug("[DEBUG] render alerts page")
    alerts = db.query(models.Alert).order_by(models.Alert.created_at.desc()).limit(100).all()
    return templates.TemplateResponse(
        request=request, name="alerts.html", context={"alerts": alerts}
    )
