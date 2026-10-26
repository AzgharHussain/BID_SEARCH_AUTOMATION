from fastapi import APIRouter, HTTPException, Query, Body, Response
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from app.services.email_service import (
    get_team_members,
    add_team_member,
    remove_team_member,
    send_email_dispatch,
    build_state_email_html,
    SENT_EMAILS_DIR,
    get_smtp_status,
    save_smtp_config,
    test_smtp_connection
)
from app.schemas.schemas import SmtpConfigPayload, SmtpTestPayload
from app.db.database import SessionLocal
from app.models import models


router = APIRouter()


class TeamMemberCreate(BaseModel):
    email: str
    name: Optional[str] = None
    role: Optional[str] = "Team Member"


class EmailDispatchPayload(BaseModel):
    recipients: List[str]
    subject: str
    state_name: Optional[str] = None
    tender_id: Optional[str] = None
    include_all_states: bool = False
    attach_zip_bundle: bool = True
    custom_notes: Optional[str] = None


@router.get("/team-members")
def list_team_members():
    """Retrieve the registered team recipient list."""
    return get_team_members()


@router.post("/team-members")
def add_new_team_member(payload: TeamMemberCreate):
    """Add a new team member recipient."""
    if not payload.email or "@" not in payload.email:
        raise HTTPException(status_code=400, detail="A valid email address is required.")
    return add_team_member(payload.email, payload.name, payload.role)


@router.delete("/team-members")
def delete_team_member(email: str = Query(..., description="Email to remove")):
    """Remove a team member recipient."""
    return remove_team_member(email)


@router.post("/send")
def send_email(payload: EmailDispatchPayload):
    """Send state and tender details with attached documents to team members."""
    if not payload.recipients:
        raise HTTPException(status_code=400, detail="At least one recipient email address is required.")
    
    try:
        result = send_email_dispatch(
            recipients=payload.recipients,
            subject=payload.subject,
            state_name=payload.state_name,
            tender_id=payload.tender_id,
            include_all_states=payload.include_all_states,
            attach_zip_bundle=payload.attach_zip_bundle,
            custom_notes=payload.custom_notes
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch email: {e}")


@router.post("/preview", response_class=HTMLResponse)
def preview_email(payload: EmailDispatchPayload):
    """Generate and return HTML preview of the email before sending."""
    db = SessionLocal()
    tenders_data = []
    state_obj = None

    try:
        if payload.tender_id:
            t = db.query(models.Tender).filter(models.Tender.tender_id == payload.tender_id).first()
            if t:
                state_obj = t.state
                tenders_data = [{
                    "tender_id": t.tender_id,
                    "title": t.title,
                    "department": t.department,
                    "published_date": t.published_date.isoformat() if t.published_date else None,
                    "last_date": t.last_date.isoformat() if t.last_date else None,
                    "portal_tender_url": t.portal_tender_url,
                    "is_live": True,
                    "is_upcoming": False,
                    "is_closing_soon": False,
                    "documents": [{
                        "id": d.id,
                        "file_name": d.file_name,
                        "file_size_kb": d.portal_size_kb,
                        "is_bundle": d.file_name.lower().endswith(".zip")
                    } for d in t.documents]
                }]
        elif payload.state_name and not payload.include_all_states:
            state_obj = db.query(models.State).filter(models.State.name == payload.state_name).first()
            if state_obj:
                for t in state_obj.tenders[:25]:
                    tenders_data.append({
                        "tender_id": t.tender_id,
                        "title": t.title,
                        "department": t.department,
                        "published_date": t.published_date.isoformat() if t.published_date else None,
                        "last_date": t.last_date.isoformat() if t.last_date else None,
                        "portal_tender_url": t.portal_tender_url,
                        "is_live": True,
                        "is_upcoming": False,
                        "is_closing_soon": False,
                        "documents": [{
                            "id": d.id,
                            "file_name": d.file_name,
                            "file_size_kb": d.portal_size_kb,
                            "is_bundle": d.file_name.lower().endswith(".zip")
                        } for d in t.documents]
                    })
        else:
            all_tenders = db.query(models.Tender).limit(30).all()
            for t in all_tenders:
                tenders_data.append({
                    "tender_id": t.tender_id,
                    "title": t.title,
                    "department": t.department,
                    "published_date": t.published_date.isoformat() if t.published_date else None,
                    "last_date": t.last_date.isoformat() if t.last_date else None,
                    "portal_tender_url": t.portal_tender_url,
                    "is_live": True,
                    "is_upcoming": False,
                    "is_closing_soon": False,
                    "documents": [{
                        "id": d.id,
                        "file_name": d.file_name,
                        "file_size_kb": d.portal_size_kb,
                        "is_bundle": d.file_name.lower().endswith(".zip")
                    } for d in t.documents]
                })
    finally:
        db.close()

    if not tenders_data:
        raise HTTPException(status_code=404, detail="No matching tenders found for preview.")

    html = build_state_email_html(
        state_name=payload.state_name,
        tenders_data=tenders_data,
        state_obj=state_obj,
        custom_notes=payload.custom_notes,
        include_all_states=payload.include_all_states
    )
    return HTMLResponse(content=html)


@router.get("/history")
def get_sent_email_history():
    """Retrieve history of dispatched emails."""
    if not SENT_EMAILS_DIR.exists():
        return []
    
    files = []
    for f in sorted(SENT_EMAILS_DIR.iterdir(), reverse=True):
        if f.suffix == ".html":
            files.append({
                "filename": f.name,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "view_url": f"/api/email/view/{f.name}"
            })
    return files[:20]


@router.get("/view/{filename}", response_class=HTMLResponse)
def view_saved_email(filename: str):
    """View a dispatched email directly in the browser."""
    clean_name = Path(filename).name
    p = SENT_EMAILS_DIR / clean_name
    if not p.exists():
        raise HTTPException(status_code=404, detail="Email archive not found.")
    with open(p, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/smtp-status")
def get_smtp_status_endpoint():
    """Retrieve current outbound email delivery mode and SMTP server configuration."""
    return get_smtp_status()


@router.post("/smtp-config")
def save_smtp_config_endpoint(payload: SmtpConfigPayload):
    """Save SMTP server settings (Gmail / custom server) to backend environment."""
    if not payload.host or not payload.user or not payload.password:
        raise HTTPException(status_code=400, detail="Host, username/email, and password are required.")
    try:
        return save_smtp_config(
            host=payload.host,
            port=payload.port,
            user=payload.user,
            password=payload.password,
            from_email=payload.from_email,
            use_tls=payload.use_tls
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update SMTP configuration: {e}")


@router.post("/test")
def test_smtp_connection_endpoint(payload: SmtpTestPayload):
    """Send an immediate verification email to test SMTP connectivity."""
    target_email = payload.target_email or "swethagisfy@gmail.com"
    res = test_smtp_connection(target_email=target_email)
    if res.get("status") == "error" or res.get("delivery_mode") != "smtp":
        raise HTTPException(
            status_code=400,
            detail=res.get("error") or res.get("message") or "SMTP delivery failed. Email was only saved locally."
        )
    return res

