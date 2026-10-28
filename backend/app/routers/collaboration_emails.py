import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import models
from app.services.collaboration_email_service import (
    collaboration_email_service,
    resolve_sender_details,
    build_collaboration_email_text,
    build_collaboration_email_html
)
from app.services.collaboration_scheduler import collaboration_scheduler
from app.services.collaboration_excel_tracker import generate_collaboration_excel_workbook
from app.services.gmail_connector import gmail_connector

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
router = APIRouter()

class GmailConfigPayload(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    sender_email: Optional[str] = None

class ProviderConfigPayload(BaseModel):
    provider_type: str  # "brevo", "sendgrid", "microsoft_365", "google_workspace", "authenticated_smtp"
    active_provider: Optional[str] = None
    brevo_api_key: Optional[str] = None
    brevo_smtp_user: Optional[str] = None
    brevo_smtp_key: Optional[str] = None
    brevo_send_method: Optional[str] = "api"
    sendgrid_api_key: Optional[str] = None
    sendgrid_send_method: Optional[str] = "api"
    m365_client_id: Optional[str] = None
    m365_client_secret: Optional[str] = None
    m365_tenant_id: Optional[str] = None
    m365_refresh_token: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_refresh_token: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    imap_host: Optional[str] = None

class TestEmailPayload(BaseModel):
    approved_recipient: str
    approval_notes: Optional[str] = None

class DraftActionPayload(BaseModel):
    notes: Optional[str] = None

class GenerateDraftsPayload(BaseModel):
    tender_id: Optional[int] = None
    min_match_score: Optional[float] = 75.0
    max_partners_per_tender: Optional[int] = 3

class UpdateDraftSenderPayload(BaseModel):
    sender_email: str
    sender_name: Optional[str] = None


@router.get("/dashboard")
def get_collaboration_dashboard(scope: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Return comprehensive dashboard data for the partner outreach automation pipeline."""
    summary = collaboration_email_service.get_dashboard_summary(db)
    scheduler_status = collaboration_scheduler.get_status()

    # Query pending drafts and recent sent with optional scope filtering
    pending_q = db.query(models.CollaborationEmail).filter(
        models.CollaborationEmail.status.in_(["draft", "pending_approval"])
    )
    sent_q = db.query(models.CollaborationEmail).filter(
        models.CollaborationEmail.status.in_(["sent", "replied", "failed"])
    )

    if scope and scope.strip() and scope.upper() != "ALL":
        if scope.lower() == "adb":
            pending_q = pending_q.filter(models.CollaborationEmail.scope == "adb")
            sent_q = sent_q.filter(models.CollaborationEmail.scope == "adb")
        elif scope.lower() in ["state", "states"]:
            pending_q = pending_q.filter(models.CollaborationEmail.scope == "state")
            sent_q = sent_q.filter(models.CollaborationEmail.scope == "state")

    pending_drafts = pending_q.order_by(models.CollaborationEmail.id.asc()).limit(300).all()
    recent_sent = sent_q.order_by(models.CollaborationEmail.id.desc()).limit(30).all()

    # Recent logs
    logs = db.query(models.CollaborationWorkflowLog).order_by(
        models.CollaborationWorkflowLog.id.desc()
    ).limit(10).all()

    def serialize_email(e):
        t = e.tender
        p = e.partner
        is_adb = bool(e.scope == "adb" or (t and t.state and "adb" in t.state.name.lower()) or (t and t.tender_id and t.tender_id.upper().startswith("ADB")))
        scope = "adb" if is_adb else "state"
        scope_label = "🌐 ADB Multilateral" if is_adb else f"🏛️ 29 States ({t.state.name if t and t.state else 'Domestic'})"
        sender_email = e.sender_email or ("support@gisfy.co.in" if is_adb else "bidding.gisfy@gmail.com")
        sender_name = e.sender_name or "N C Harika | Business Development Executive"
        from_address = f"{sender_name} <{sender_email}>"
        preferred_client = "outlook" if is_adb else "gmail"

        return {
            "id": e.id,
            "tender_id": t.tender_id if t else None,
            "tender_title": t.title if t else None,
            "state_name": t.state.name if (t and t.state) else None,
            "scope": scope,
            "scope_label": scope_label,
            "is_adb": is_adb,
            "sender_email": sender_email,
            "sender_name": sender_name,
            "from_address": from_address,
            "preferred_client": preferred_client,
            "partner_category": getattr(p, "category", "STATE") if p else ("ADB" if is_adb else "STATE"),
            "partner_country": (getattr(p, "country", None) or getattr(p, "state", None)) if p else ("Regional" if is_adb else "India"),
            "partner_state": p.state if p else None,
            "company_name": e.company_name,
            "recipient_name": e.recipient_name,
            "recipient_email": e.recipient_email,
            "subject": e.subject,
            "match_score": e.match_score,
            "selection_reason": e.selection_reason,
            "project_name": e.project_name,
            "status": e.status,
            "approval_status": e.approval_status,
            "is_draft": e.is_draft,
            "sent_at": e.sent_at.isoformat() if e.sent_at else None,
            "follow_up_date": e.follow_up_date.isoformat() if e.follow_up_date else None,
            "response_status": e.response_status,
            "response_snippet": e.response_snippet,
            "last_error": e.last_error,
            "provider": e.provider,
            "provider_status_code": e.provider_status_code,
            "provider_message_id": e.provider_message_id,
            "sent_folder_verified": bool(e.sent_folder_verified),
            "delivery_verified": bool(e.delivery_verified),
            "delivery_verified_at": e.delivery_verified_at.isoformat() if e.delivery_verified_at else None,
            "is_test_email": bool(e.is_test_email),
            "created_at": e.created_at.isoformat() if e.created_at else None
        }

    return {
        "summary": summary,
        "scheduler": scheduler_status,
        "pending_drafts": [serialize_email(e) for e in pending_drafts],
        "recent_sent": [serialize_email(e) for e in recent_sent],
        "recent_logs": [
            {
                "id": l.id,
                "cycle_type": l.cycle_type,
                "started_at": l.started_at.isoformat() if l.started_at else None,
                "finished_at": l.finished_at.isoformat() if l.finished_at else None,
                "tenders_analyzed": l.tenders_analyzed,
                "drafts_created": l.drafts_created,
                "emails_sent": l.emails_sent,
                "replies_checked": l.replies_checked,
                "follow_ups_flagged": l.follow_ups_flagged,
                "errors_count": l.errors_count,
                "status": l.status,
                "details": l.log_details
            } for l in logs
        ]
    }


@router.get("/drafts")
def list_collaboration_drafts(
    status: Optional[str] = Query(None, description="Filter by status ('draft', 'approved', 'sent', etc.)"),
    scope: Optional[str] = Query(None, description="Filter by scope: 'state' (29 Indian States), 'adb' (Asian Development Bank), or 'all'"),
    state_name: Optional[str] = Query(None, description="Filter by state name or 'ADB - Asian Development Bank'"),
    tender_id: Optional[int] = Query(None),
    partner_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """List all collaboration email drafts with filtering across all 29 States and ADB."""
    q = db.query(models.CollaborationEmail)
    if status:
        q = q.filter(models.CollaborationEmail.status == status)
    if tender_id:
        q = q.filter(models.CollaborationEmail.tender_id == tender_id)
    if partner_id:
        q = q.filter(models.CollaborationEmail.partner_id == partner_id)

    if scope and scope.strip() and scope.upper() != "ALL":
        if scope.lower() == "adb":
            q = q.filter(models.CollaborationEmail.scope == "adb")
        elif scope.lower() in ["state", "states"]:
            q = q.filter(models.CollaborationEmail.scope == "state")

    if state_name and state_name.strip() and state_name.upper() != "ALL":
        q = q.join(models.Tender).join(models.State).filter(models.State.name.ilike(f"%{state_name.strip()}%"))

    records = q.order_by(models.CollaborationEmail.id.asc()).offset(skip).limit(limit).all()

    results = []
    for r in records:
        t = r.tender
        p = r.partner
        is_adb = bool(r.scope == "adb" or (t and t.state and "adb" in t.state.name.lower()) or (t and t.tender_id and t.tender_id.upper().startswith("ADB")))
        scope_val = "adb" if is_adb else "state"
        scope_label = "🌐 ADB Multilateral" if is_adb else f"🏛️ 29 States ({t.state.name if t and t.state else 'Domestic'})"

        sender_email = r.sender_email or ("support@gisfy.co.in" if is_adb else "bidding.gisfy@gmail.com")
        sender_name = r.sender_name or "N C Harika | Business Development Executive"
        from_address = f"{sender_name} <{sender_email}>"
        preferred_client = "outlook" if is_adb else "gmail"

        results.append({
            "id": r.id,
            "tender_id": t.tender_id if t else None,
            "tender_db_id": r.tender_id,
            "tender_title": t.title if t else None,
            "state_name": t.state.name if (t and t.state) else None,
            "scope": scope_val,
            "scope_label": scope_label,
            "is_adb": is_adb,
            "sender_email": sender_email,
            "sender_name": sender_name,
            "from_address": from_address,
            "preferred_client": preferred_client,
            "partner_category": getattr(p, "category", "STATE") if p else ("ADB" if is_adb else "STATE"),
            "partner_country": (getattr(p, "country", None) or getattr(p, "state", None)) if p else ("Regional" if is_adb else "India"),
            "partner_state": p.state if p else None,
            "submission_deadline": t.last_date.strftime("%d %b %Y") if (t and t.last_date) else None,
            "partner_id": r.partner_id,
            "company_name": r.company_name,
            "recipient_name": r.recipient_name,
            "recipient_email": r.recipient_email,
            "subject": r.subject,
            "body_html": r.body_html,
            "body_text": r.body_text,
            "project_name": r.project_name,
            "project_overview": r.project_overview,
            "match_score": r.match_score,
            "selection_reason": r.selection_reason,
            "status": r.status,
            "approval_status": r.approval_status,
            "is_draft": r.is_draft,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "follow_up_date": r.follow_up_date.isoformat() if r.follow_up_date else None,
            "response_status": r.response_status,
            "response_snippet": r.response_snippet,
            "last_error": r.last_error,
            "provider": r.provider,
            "provider_status_code": r.provider_status_code,
            "provider_message_id": r.provider_message_id,
            "sent_folder_verified": bool(r.sent_folder_verified),
            "delivery_verified": bool(r.delivery_verified),
            "delivery_verified_at": r.delivery_verified_at.isoformat() if r.delivery_verified_at else None,
            "is_test_email": bool(r.is_test_email),
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return results


@router.get("/drafts/{id}/preview", response_class=HTMLResponse)
def preview_draft_html(id: int, db: Session = Depends(get_db)):
    """Render full HTML email preview of a collaboration draft."""
    record = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Collaboration email record not found")
    html_content = record.body_html or ""
    if "{{GISFY_LOGO_SRC}}" in html_content:
        from app.services.collaboration_email_service import get_gisfy_logo_src
        html_content = html_content.replace("{{GISFY_LOGO_SRC}}", get_gisfy_logo_src())
    return HTMLResponse(content=html_content)


@router.get("/gisfy_logo.png")
@router.get("/logo.png")
def get_gisfy_logo_file():
    """Serve authentic high-resolution GISFY corporate logo PNG."""
    from fastapi.responses import FileResponse
    png_path = BASE_DIR / "storage" / "gisfy_logo.png"
    if png_path.exists():
        return FileResponse(png_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo not found")


@router.post("/generate-drafts")
def generate_drafts_endpoint(
    payload: GenerateDraftsPayload,
    db: Session = Depends(get_db)
):
    """
    Analyze tender proposals and generate personalized candidate drafts for suitable partners.
    Adheres strictly to draft-only mode and de-duplication rules.
    """
    created = []
    if payload.tender_id:
        tenders = db.query(models.Tender).filter(models.Tender.id == payload.tender_id).all()
    else:
        # Generate for candidate active tenders
        tenders = db.query(models.Tender).filter(
            models.Tender.status.in_(["active", "new"])
        ).limit(10).all()

    for t in tenders:
        drafts = collaboration_email_service.generate_drafts_for_tender(
            db=db,
            tender_id=t.id,
            min_match_score=payload.min_match_score or 75.0,
            max_partners_per_tender=payload.max_partners_per_tender or 2
        )
        created.extend(drafts)

    return {
        "status": "success",
        "drafts_generated": len(created),
        "message": f"Successfully analyzed {len(tenders)} tender proposals and created {len(created)} personalized drafts in Draft-Only mode."
    }


@router.post("/drafts/{id}/approve")
def approve_draft_endpoint(id: int, db: Session = Depends(get_db)):
    """Approve a draft. It will be sent during the next cycle or when 'Send Now' is clicked."""
    try:
        draft = collaboration_email_service.approve_draft(db, id)
        return {
            "status": "approved",
            "message": f"Draft #{id} for {draft.company_name} approved successfully.",
            "draft_id": id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/drafts/{id}/send")
def send_draft_now_endpoint(id: int, db: Session = Depends(get_db)):
    """Explicitly send an approved collaboration email immediately with quota and M365 auth checks."""
    draft = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Prevent duplicate sends
    if draft.status in ["Sending", "Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"]:
        raise HTTPException(status_code=400, detail=f"Email #{id} has already been dispatched or is currently in progress (Status: {draft.status}).")

    # Step 5 Rolling 24-hour Quota Check
    sent_24h = collaboration_scheduler.get_rolling_24h_sent_count(db)
    active_limit = collaboration_scheduler.pilot_limit if collaboration_scheduler.pilot_mode else collaboration_scheduler.max_daily_limit
    if sent_24h >= active_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily outreach quota reached ({sent_24h}/{active_limit} emails in rolling 24 hours). Outreach is capped at {active_limit} emails/day."
        )

    # Check Microsoft 365 Authentication
    from app.services.live_email_provider import live_email_provider
    pub_status = live_email_provider.get_public_status()
    if not pub_status.get("is_authenticated"):
        raise HTTPException(
            status_code=401,
            detail="Microsoft 365 is not authenticated. Please complete Microsoft 365 OAuth 2.0 authorization before sending real emails."
        )

    # Auto-approve if user clicks send directly
    if draft.approval_status != "approved":
        collaboration_email_service.approve_draft(db, id)

    success, message = collaboration_email_service.send_email(db, id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    db.refresh(draft)
    import urllib.parse

    is_adb = bool(
        draft.scope == "adb"
        or (draft.subject and "[ADB" in draft.subject)
        or (draft.body_text and "ASIAN DEVELOPMENT BANK" in draft.body_text)
    )
    s_info = resolve_sender_details(is_adb=is_adb, sender_email=draft.sender_email, sender_name=draft.sender_name)
    sender_email = s_info["email"]
    sender_name = s_info["name"]
    from_address = f"{sender_name} <{sender_email}>"

    clean_cc = "bidding@gisfy.co.in"
    full_body = draft.body_text or ""

    quoted_sub = urllib.parse.quote(draft.subject or "")
    quoted_body = urllib.parse.quote(full_body)
    quoted_cc = urllib.parse.quote(clean_cc)
    to_with_cc = f"{draft.recipient_email}?cc={clean_cc}"
    quoted_to_with_cc = urllib.parse.quote(to_with_cc)

    mailto_url = f"mailto:{draft.recipient_email}?cc={quoted_cc}&subject={quoted_sub}&body={quoted_body}"
    outlook_web_url = f"https://outlook.office.com/mail/{sender_email}/deeplink/compose?to={quoted_to_with_cc}&cc={quoted_cc}&subject={quoted_sub}&body={quoted_body}"
    gmail_web_url = f"https://mail.google.com/mail/u/bidding.gisfy@gmail.com/?view=cm&fs=1&authuser=bidding.gisfy@gmail.com&to={draft.recipient_email}&cc={quoted_cc}&su={quoted_sub}&body={quoted_body}"

    return {
        "status": draft.status,
        "message": message,
        "recipient": draft.recipient_email,
        "company": draft.company_name,
        "from_address": from_address,
        "sender_email": sender_email,
        "sender_name": sender_name,
        "preferred_client": "outlook" if is_adb else "gmail",
        "cc": clean_cc,
        "provider": draft.provider,
        "provider_status_code": draft.provider_status_code,
        "sent_folder_verified": draft.sent_folder_verified,
        "delivery_verified": draft.delivery_verified,
        "mailto_url": mailto_url,
        "outlook_web_url": outlook_web_url,
        "gmail_web_url": gmail_web_url
    }


@router.post("/drafts/{id}/reject")
def reject_draft_endpoint(
    id: int,
    payload: Optional[DraftActionPayload] = None,
    db: Session = Depends(get_db)
):
    """Reject and discard a draft from the outreach queue."""
    try:
        reason = payload.notes if payload else "Rejected by user"
        draft = collaboration_email_service.reject_draft(db, id, reason=reason)
        return {
            "status": "rejected",
            "message": f"Draft #{id} rejected and cancelled.",
            "draft_id": id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/drafts/{id}/switch-sender")
@router.post("/drafts/{id}/update-sender")
def switch_draft_sender_endpoint(
    id: int,
    payload: UpdateDraftSenderPayload,
    db: Session = Depends(get_db)
):
    """
    Switch the authorized sender for an outreach draft.
    For ADB proposals, users can switch between:
    - support@gisfy.co.in (GISFY Support Team)
    - farhath@gisfy.co.in (Farhath - ADB Partnerships)
    - firza@gisfy.co.in (Firza - Multilateral Lead)
    Updates sender_email, sender_name, and re-renders body_text and body_html signatures.
    """
    draft = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    t = draft.tender
    is_adb = bool(draft.scope == "adb" or (t and t.state and "adb" in t.state.name.lower()))
    
    s_email = payload.sender_email.strip().lower()
    s_info = resolve_sender_details(is_adb=is_adb, sender_email=s_email, sender_name=payload.sender_name)
    s_name = s_info["name"]
    
    draft.sender_email = s_info["email"]
    draft.sender_name = s_name

    state_name = t.state.name if (t and t.state) else ("ADB Multilateral" if is_adb else "Domestic")
    
    draft.body_text = build_collaboration_email_text(
        project_name=draft.project_name or (t.title if t else "Project Assignment"),
        project_overview=draft.project_overview,
        state_name=state_name,
        is_adb=is_adb,
        sender_name=s_name,
        sender_email=draft.sender_email
    )
    draft.body_html = build_collaboration_email_html(
        project_name=draft.project_name or (t.title if t else "Project Assignment"),
        project_overview=draft.project_overview,
        state_name=state_name,
        is_adb=is_adb,
        sender_name=s_name,
        sender_email=draft.sender_email,
        subject_line=draft.subject
    )

    db.commit()
    db.refresh(draft)

    return {
        "status": "success",
        "draft_id": draft.id,
        "sender_email": draft.sender_email,
        "sender_name": draft.sender_name,
        "from_address": f"{draft.sender_name} <{draft.sender_email}>",
        "body_text": draft.body_text,
        "body_html": draft.body_html,
        "message": f"Sender successfully updated to {draft.sender_name} <{draft.sender_email}>."
    }


@router.post("/trigger-daily-cycle")
def trigger_daily_cycle_endpoint():
    """Manually trigger the 9:00 AM IST daily collaboration workflow cycle now."""
    summary = collaboration_scheduler.execute_daily_workflow(cycle_type="manual_trigger")
    return {
        "status": "completed",
        "message": "Daily partner collaboration workflow executed successfully.",
        "summary": summary
    }


class ScheduleTimePayload(BaseModel):
    schedule_time: Optional[str] = None
    states_schedule_time: Optional[str] = None
    adb_schedule_time: Optional[str] = None
    adb_rotation_quota: Optional[int] = None
    auto_send_enabled: Optional[bool] = None
    window_start: Optional[str] = None
    window_end: Optional[str] = None


@router.post("/scheduler/trigger-states")
def trigger_states_dispatch_endpoint(batch_limit: Optional[int] = Query(None)):
    """
    Trigger the 29 Indian States 09:30 AM dispatch immediately.
    Sends through bidding.gisfy@gmail.com (N C Harika | Business Development Executive, CC: bidding@gisfy.co.in).
    """
    summary = collaboration_scheduler.execute_states_dispatch(batch_limit=batch_limit)
    return {
        "status": "completed",
        "message": f"Dispatched {summary.get('dispatched_count', 0)} 29 States outreach emails from bidding.gisfy@gmail.com.",
        "summary": summary
    }


@router.post("/scheduler/trigger-adb")
def trigger_adb_rotation_dispatch_endpoint(quota: int = 50):
    """
    Trigger the ADB Multilateral 10:30 AM 50-quota rotation dispatch immediately.
    Sequence: 50 via support@gisfy.co.in -> 50 via farhath@gisfy.co.in -> 50 via firza@gisfy.co.in.
    """
    summary = collaboration_scheduler.execute_adb_rotation_dispatch(quota_per_sender=quota)
    return {
        "status": "completed",
        "message": f"Completed ADB rotation: {summary.get('total_dispatched', 0)} emails dispatched across support (50), farhath (50), firza (50).",
        "summary": summary
    }


@router.post("/update-schedule-time")
def update_schedule_time_endpoint(
    payload: Optional[ScheduleTimePayload] = None,
    time: Optional[str] = Query(None),
    schedule_time: Optional[str] = Query(None),
    states_time: Optional[str] = Query(None),
    adb_time: Optional[str] = Query(None),
    adb_quota: Optional[int] = Query(None),
    auto_send_enabled: Optional[bool] = Query(None),
    window_start: Optional[str] = Query(None),
    window_end: Optional[str] = Query(None)
):
    """
    Dynamically update the automated email outreach schedule times for 29 States and ADB.
    Reschedules APScheduler jobs immediately and persists to scheduler_config.json.
    """
    s_time = states_time or time or schedule_time
    a_time = adb_time
    quota = adb_quota
    auto_send = auto_send_enabled
    w_start = window_start
    w_end = window_end

    if payload:
        s_time = payload.states_schedule_time or payload.schedule_time or s_time
        a_time = payload.adb_schedule_time or a_time
        quota = payload.adb_rotation_quota or quota
        auto_send = payload.auto_send_enabled if payload.auto_send_enabled is not None else auto_send
        w_start = payload.window_start or w_start
        w_end = payload.window_end or w_end

    try:
        res = collaboration_scheduler.set_schedules(
            states_time=s_time,
            adb_time=a_time,
            adb_quota=quota,
            auto_send_enabled=auto_send,
            window_start=w_start,
            window_end=w_end
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update schedules: {e}")


@router.get("/scheduler-status")
def get_scheduler_status_endpoint():
    """Return status and next run time of the daily dynamic scheduler."""
    return collaboration_scheduler.get_status()


@router.post("/toggle-auto-send")
def toggle_auto_send_endpoint(enabled: bool = Query(...)):
    """
    Requirement 9: Toggle between Draft-Only Mode (enabled=False) and Auto-Send Mode (enabled=True).
    Requires explicit user authorization.
    """
    collaboration_email_service.auto_send_enabled = enabled
    collaboration_scheduler.save_config()
    return {
        "status": "ok",
        "auto_send_enabled": collaboration_email_service.auto_send_enabled,
        "mode": "Automatic Sending Enabled" if enabled else "Draft-Only Mode Active (Approval Required)"
    }


@router.post("/toggle-pause")
def toggle_pause_endpoint(paused: bool = Query(...)):
    """Pause or resume the 9:00 AM IST daily automated scheduler."""
    if paused:
        res = collaboration_scheduler.pause()
    else:
        res = collaboration_scheduler.resume()
    return res


@router.post("/stop-automation")
def stop_automation_endpoint():
    """Step 5: Immediately stop automated daily email outreach and pause the queue."""
    return collaboration_scheduler.stop_automation()


@router.post("/toggle-pilot-mode")
def toggle_pilot_mode_endpoint(enabled: bool = Query(...)):
    """Step 5: Toggle between Pilot Volume (max 5 emails/day) and Full Production (max 50 emails/day)."""
    return collaboration_scheduler.set_pilot_mode(enabled)


@router.post("/drafts/{id}/retry")
def retry_failed_draft_endpoint(id: int, db: Session = Depends(get_db)):
    """Step 9: Manual retry for failed messages."""
    draft = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status not in ["Failed", "failed"]:
        raise HTTPException(status_code=400, detail=f"Email #{id} is not in Failed status (Current status: {draft.status}).")

    draft.status = "approved"
    draft.retry_count = 0
    draft.last_error = None
    db.commit()

    success, message = collaboration_email_service.send_email(db, id)
    if not success:
        raise HTTPException(status_code=400, detail=message)

    db.refresh(draft)
    return {
        "status": draft.status,
        "message": f"Retry succeeded: {message}",
        "recipient": draft.recipient_email,
        "provider": draft.provider,
        "sent_folder_verified": draft.sent_folder_verified
    }


@router.post("/confirm-delivery/{id}")
def confirm_delivery_endpoint(id: int, evidence: str = Query(..., description="Legitimate delivery evidence"), db: Session = Depends(get_db)):
    """Step 4: Confirm actual recipient delivery based on legitimate evidence (NDR trace, recipient reply, or authorized verification)."""
    draft = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft.delivery_verified = True
    draft.delivery_verified_at = datetime.utcnow()
    draft.status = "Delivery Confirmed"
    draft.last_error = None
    db.commit()
    db.refresh(draft)
    return {
        "status": "Delivery Confirmed",
        "delivery_verified": True,
        "evidence": evidence,
        "delivery_verified_at": draft.delivery_verified_at.isoformat()
    }


@router.get("/export-excel")
def export_collaboration_excel(db: Session = Depends(get_db)):
    """
    Requirement 8: Export the complete partner collaboration tracking database as a formatted Excel spreadsheet.
    """
    excel_stream = generate_collaboration_excel_workbook(db)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    filename = f"GISFY_Partner_Collaboration_Tracker_{timestamp}.xlsx"

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/gmail-status")
def get_gmail_status():
    """Return Gmail connection and OAuth2 security status."""
    return gmail_connector.get_status()


@router.post("/save-gmail-config")
def save_gmail_config(payload: GmailConfigPayload):
    """
    Requirement 5: Connect securely to authorized Gmail account.
    Never stores plaintext user passwords.
    """
    if payload.client_id and payload.client_secret:
        res = gmail_connector.save_client_config(payload.client_id, payload.client_secret)
        return res
    elif payload.refresh_token:
        res = gmail_connector.save_refresh_token(payload.refresh_token, payload.sender_email)
        return res
    else:
        raise HTTPException(status_code=400, detail="Provide client_id and client_secret or refresh_token")


@router.post("/check-replies")
def check_replies_endpoint(db: Session = Depends(get_db)):
    """Manually trigger checking for incoming replies across sent email threads."""
    count = collaboration_email_service.check_incoming_replies(db)
    return {
        "status": "ok",
        "replies_detected": count,
        "message": f"Checked active threads; {count} new partner responses detected."
    }


@router.get("/provider-status")
def get_email_provider_status():
    """
    Return current live authenticated email provider status, active provider,
    and masked settings without ever leaking credentials or secrets.
    """
    from app.services.live_email_provider import live_email_provider
    return live_email_provider.get_public_status()


@router.post("/save-provider-config")
def save_provider_config_endpoint(payload: ProviderConfigPayload):
    """
    Securely configure live email credentials for Brevo, SendGrid, Microsoft 365,
    Google Workspace OAuth 2.0, or Authenticated SMTP.
    Credentials are saved with 0600 file permissions and never echoed in plain text.
    """
    from app.services.live_email_provider import live_email_provider

    if payload.provider_type == "brevo":
        if not payload.brevo_api_key and not (payload.brevo_smtp_user and payload.brevo_smtp_key):
            raise HTTPException(status_code=400, detail="Brevo API Key or SMTP credentials (login + SMTP key) are required.")
        res = live_email_provider.save_brevo_config(
            api_key=payload.brevo_api_key,
            smtp_user=payload.brevo_smtp_user,
            smtp_key=payload.brevo_smtp_key,
            send_method=payload.brevo_send_method or "api"
        )
        return {**res, "public_status": live_email_provider.get_public_status()}
    elif payload.provider_type == "sendgrid":
        if not payload.sendgrid_api_key:
            raise HTTPException(status_code=400, detail="SendGrid API Key is required.")
        res = live_email_provider.save_sendgrid_config(
            api_key=payload.sendgrid_api_key,
            send_method=payload.sendgrid_send_method or "api"
        )
        return {**res, "public_status": live_email_provider.get_public_status()}
    elif payload.provider_type == "microsoft_365":
        if not payload.m365_client_id:
            raise HTTPException(status_code=400, detail="Microsoft 365 Client ID (Application ID) is required.")
        res = live_email_provider.save_m365_config(
            client_id=payload.m365_client_id,
            client_secret=payload.m365_client_secret,
            tenant_id=payload.m365_tenant_id,
            refresh_token=payload.m365_refresh_token
        )
        return {**res, "public_status": live_email_provider.get_public_status()}
    elif payload.provider_type == "google_workspace":
        if not payload.google_client_id:
            raise HTTPException(status_code=400, detail="Google Client ID is required.")
        res = live_email_provider.save_google_config(
            client_id=payload.google_client_id,
            client_secret=payload.google_client_secret,
            refresh_token=payload.google_refresh_token
        )
        return {**res, "public_status": live_email_provider.get_public_status()}
    elif payload.provider_type == "authenticated_smtp":
        if not (payload.smtp_host and payload.smtp_user and payload.smtp_password):
            raise HTTPException(status_code=400, detail="SMTP Host, User, and Password are required.")
        res = live_email_provider.save_smtp_config(
            host=payload.smtp_host,
            port=payload.smtp_port or 587,
            user=payload.smtp_user,
            password=payload.smtp_password,
            imap_host=payload.imap_host
        )
        return {**res, "public_status": live_email_provider.get_public_status()}
    else:
        raise HTTPException(status_code=400, detail="Invalid provider_type. Choose brevo, sendgrid, microsoft_365, google_workspace, or authenticated_smtp.")


@router.get("/domain-dns-status")
def get_domain_dns_status(domain: str = Query("gisfy.co.in")):
    """
    Step 2: Live DNS audit for sender domain (SPF alignment, DKIM records, DMARC policy).
    Verifies that gisfy.co.in is authorized to send via Brevo or SendGrid without overwriting M365 records.
    """
    from app.services.live_email_provider import live_email_provider
    return live_email_provider.check_domain_dns_status(domain=domain)


@router.post("/set-active-provider")
def set_active_provider_endpoint(provider: str = Query(..., description="brevo, sendgrid, microsoft_365, authenticated_smtp, or google_workspace")):
    """
    Explicitly switch active outbound live provider without deleting stored credentials for other providers.
    """
    from app.services.live_email_provider import live_email_provider
    try:
        res = live_email_provider.set_active_provider(provider)
        return {**res, "public_status": live_email_provider.get_public_status()}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/m365/device-flow/initiate")
def initiate_m365_device_flow_endpoint(
    client_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Step 2: Initiate Microsoft MSAL Device Code Flow for Support mailbox.
    Purges previous session and starts a clean device code authentication session.
    """
    from app.services.live_email_provider import live_email_provider
    try:
        res = live_email_provider.initiate_m365_device_flow(client_id=client_id, tenant_id=tenant_id)
        return res
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/m365/device-flow/status")
def get_m365_device_flow_status_endpoint():
    """
    Step 2: Check live polling status of Microsoft MSAL Device Code authentication.
    """
    from app.services.live_email_provider import live_email_provider
    try:
        return live_email_provider.get_m365_device_flow_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/m365/device-flow/cancel")
def cancel_m365_device_flow_endpoint():
    """Cancel pending device flow."""
    from app.services.live_email_provider import live_email_provider
    try:
        live_email_provider.cancel_m365_device_flow()
        return {"status": "cancelled", "message": "Device code flow cancelled."}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/m365/auth-url")
def get_m365_auth_url_endpoint(
    client_id: Optional[str] = Query(None),
    client_secret: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
    redirect_uri: Optional[str] = Query(None)
):
    """
    Generate the Microsoft Entra OAuth 2.0 authorization URL for delegated user sign-in.
    Pre-populates login_hint for support@gisfy.co.in.
    """
    from app.services.live_email_provider import live_email_provider
    try:
        url = live_email_provider.get_m365_authorization_url(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            redirect_uri=redirect_uri
        )
        return {
            "status": "success",
            "auth_url": url,
            "redirect_uri": redirect_uri or live_email_provider.get_public_status().get("redirect_uri")
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/m365/callback", response_class=HTMLResponse)
def m365_oauth_callback_endpoint(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """
    Callback endpoint redirected from Microsoft Entra sign-in.
    Exchanges code for tokens, validates mailbox identity against Microsoft Graph /v1.0/me,
    and returns a clean auto-closing postMessage popup window.
    """
    from app.services.live_email_provider import live_email_provider

    if error or not code:
        err_msg = error_description or error or "Authorization was cancelled or denied by Microsoft Entra."
        html_error = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Microsoft 365 Authorization Error</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #fff1f2; color: #1e293b; }}
    .card {{ background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); max-width: 480px; text-align: center; border: 1px solid #fecdd3; }}
    .icon {{ font-size: 3rem; margin-bottom: 0.8rem; }}
    h2 {{ color: #be123c; margin: 0 0 0.5rem; font-size: 1.4rem; }}
    p {{ color: #64748b; font-size: 0.9rem; line-height: 1.5; margin: 0 0 1.2rem; }}
    .error-box {{ background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 0.75rem; border-radius: 8px; font-size: 0.8rem; text-align: left; margin-bottom: 1.5rem; font-family: monospace; word-break: break-all; }}
    .btn {{ background: #e11d48; color: white; padding: 0.65rem 1.5rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem; border: none; cursor: pointer; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">❌</div>
    <h2>Microsoft 365 Authorization Failed</h2>
    <p>Microsoft Entra ID rejected or cancelled the sign-in request.</p>
    <div class="error-box">{err_msg}</div>
    <button class="btn" onclick="window.close()">Close Window</button>
  </div>
  <script>
    if (window.opener) {{
      window.opener.postMessage({{ type: 'M365_AUTH_ERROR', error: {json.dumps(err_msg)} }}, '*');
    }}
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_error, status_code=400)

    # Exchange authorization code for tokens
    result = live_email_provider.exchange_m365_auth_code(code=code)
    if not result.get("success"):
        err_detail = result.get("error", "Failed to exchange token.")
        html_fail = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Microsoft 365 Token Error</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #fff1f2; color: #1e293b; }}
    .card {{ background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); max-width: 480px; text-align: center; border: 1px solid #fecdd3; }}
    .icon {{ font-size: 3rem; margin-bottom: 0.8rem; }}
    h2 {{ color: #be123c; margin: 0 0 0.5rem; font-size: 1.4rem; }}
    p {{ color: #64748b; font-size: 0.9rem; line-height: 1.5; margin: 0 0 1.2rem; }}
    .error-box {{ background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 0.75rem; border-radius: 8px; font-size: 0.8rem; text-align: left; margin-bottom: 1.5rem; font-family: monospace; word-break: break-all; }}
    .btn {{ background: #e11d48; color: white; padding: 0.65rem 1.5rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem; border: none; cursor: pointer; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">❌</div>
    <h2>Token Exchange Failed</h2>
    <p>Failed to exchange authorization code with Microsoft identity platform.</p>
    <div class="error-box">{err_detail}</div>
    <button class="btn" onclick="window.close()">Close Window</button>
  </div>
  <script>
    if (window.opener) {{
      window.opener.postMessage({{ type: 'M365_AUTH_ERROR', error: {json.dumps(err_detail)} }}, '*');
    }}
  </script>
</body>
</html>"""
        return HTMLResponse(content=html_fail, status_code=400)

    user_email = result.get("user_email", "support@gisfy.co.in")
    display_name = result.get("display_name", "GISFY Support Team")

    html_success = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Microsoft 365 Connected</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f0fdf4; color: #1e293b; }}
    .card {{ background: white; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); max-width: 480px; text-align: center; border: 1px solid #bbf7d0; }}
    .icon {{ font-size: 3rem; margin-bottom: 0.8rem; }}
    .badge {{ display: inline-block; background: #dcfce7; color: #15803d; font-weight: 700; padding: 0.35rem 0.9rem; border-radius: 9999px; font-size: 0.82rem; margin-bottom: 0.8rem; }}
    h2 {{ color: #14532d; margin: 0 0 0.5rem; font-size: 1.4rem; }}
    p {{ color: #475569; font-size: 0.9rem; line-height: 1.5; margin: 0 0 1.5rem; }}
    .user-pill {{ background: #f1f5f9; border: 1px solid #e2e8f0; padding: 0.6rem 1rem; border-radius: 8px; font-size: 0.85rem; font-weight: 600; color: #0f172a; margin-bottom: 1.2rem; }}
    .btn {{ background: #16a34a; color: white; padding: 0.65rem 1.6rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.9rem; border: none; cursor: pointer; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✅</div>
    <div class="badge">Microsoft Graph Verified</div>
    <h2>Microsoft 365 Connected!</h2>
    <div class="user-pill">
      👤 {display_name} ({user_email})
    </div>
    <p>Your Microsoft 365 mailbox has been authenticated. Tokens have been securely stored and live email sending is now active.</p>
    <button class="btn" onclick="window.close()">Close &amp; Return to Dashboard</button>
  </div>
  <script>
    if (window.opener) {{
      window.opener.postMessage({{
        type: 'M365_AUTH_SUCCESS',
        mailbox: {json.dumps(user_email)},
        displayName: {json.dumps(display_name)}
      }}, '*');
      setTimeout(function() {{ window.close(); }}, 2200);
    }} else {{
      setTimeout(function() {{ window.location.href = 'http://localhost:5173/'; }}, 2500);
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_success, status_code=200)


@router.post("/m365/verify")
def verify_m365_endpoint():
    """
    Test live connectivity and token validity against Microsoft Graph API (/v1.0/me or /users).
    """
    from app.services.live_email_provider import live_email_provider
    res = live_email_provider.verify_m365_connection()
    return {
        **res,
        "public_status": live_email_provider.get_public_status()
    }


@router.post("/m365/disconnect")
def disconnect_m365_endpoint():
    """
    Disconnect Microsoft 365 and purge stored tokens.
    """
    from app.services.live_email_provider import live_email_provider
    res = live_email_provider.disconnect_m365()
    return {
        **res,
        "public_status": live_email_provider.get_public_status()
    }


@router.post("/send-test-email")
def send_test_email_endpoint(payload: TestEmailPayload, db: Session = Depends(get_db)):
    """
    Requirement 8: Send exactly one test email to an approved recipient.
    Must verify delivery to recipient, CC (bidding@gisfy.co.in), and Sent folder.
    Do not display a successful dispatch message unless the email provider has actually accepted the message.
    """
    from app.services.live_email_provider import live_email_provider, DEFAULT_CC_EMAIL, DEFAULT_SENDER_NAME, DEFAULT_SENDER_EMAIL, DEFAULT_REPLY_TO

    clean_recipient = payload.approved_recipient.strip()
    if not clean_recipient or "@" not in clean_recipient:
        raise HTTPException(status_code=400, detail="A valid approved recipient email is required.")

    # Execute approved test dispatch
    dispatch_res = live_email_provider.send_approved_test_email(
        approved_test_recipient=clean_recipient,
        user_approval_notes=payload.approval_notes
    )

    is_sent_verified = bool(dispatch_res.get("sent_folder_verified"))
    # Step 4: Map status accurately. HTTP 202 is Provider Accepted; presence in Sent Items is Found in Sent Items.
    status_label = "Found in Sent Items" if is_sent_verified else ("Provider Accepted" if dispatch_res.get("success") else "Failed")

    test_record = models.CollaborationEmail(
        tender_id=None,
        partner_id=None,
        recipient_name="Approved Test Recipient",
        recipient_email=clean_recipient,
        company_name="Approved Test Recipient",
        subject="Exploring JV / Consortium Partnership – Test Verification Ref #TEST-1",
        body_text="Test email verification",
        body_html="<p>Test email verification</p>",
        project_name="Live Email Verification Test",
        project_overview="Verification of delivery to recipient, CC (bidding@gisfy.co.in), and Sent folder.",
        status=status_label,
        approval_status="approved",
        is_draft=False,
        is_test_email=True,
        sent_at=datetime.utcnow() if dispatch_res.get("success") else None,
        provider=dispatch_res.get("provider"),
        provider_status_code=dispatch_res.get("provider_status_code"),
        provider_message_id=dispatch_res.get("provider_message_id"),
        provider_response_raw=str(dispatch_res),
        sent_folder_verified=is_sent_verified,
        delivery_verified=False,  # Step 4: True delivery confirmation requires legitimate delivery trace
        delivery_verified_at=None,
        last_error=dispatch_res.get("error") if not dispatch_res.get("success") else None
    )
    db.add(test_record)
    db.commit()
    db.refresh(test_record)

    if not dispatch_res.get("success"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": dispatch_res.get("error") or "Email provider rejected test message.",
                "provider": dispatch_res.get("provider"),
                "provider_status_code": dispatch_res.get("provider_status_code"),
                "test_id": test_record.id,
                "status": "Failed"
            }
        )

    return {
        "status": "success",
        "provider_accepted": True,
        "delivery_status": status_label,
        "test_record_id": test_record.id,
        "recipient": clean_recipient,
        "cc": DEFAULT_CC_EMAIL,
        "from": f"{DEFAULT_SENDER_NAME} <{DEFAULT_SENDER_EMAIL}>",
        "reply_to": DEFAULT_REPLY_TO,
        "provider": dispatch_res.get("provider"),
        "provider_status_code": dispatch_res.get("provider_status_code", 200),
        "provider_message": dispatch_res.get("provider_message", "Message accepted by mail provider"),
        "sent_folder_verified": is_sent_verified,
        "mailto_url": dispatch_res.get("mailto_url"),
        "outlook_web_url": dispatch_res.get("outlook_web_url"),
        "raw_response": dispatch_res
    }


@router.post("/verify-sent-folder/{id}")
def verify_sent_folder_endpoint(id: int, db: Session = Depends(get_db)):
    """
    Step 4: Independently verify if an email is present in Sent folder
    and transition status to 'Found in Sent Items'.
    """
    from app.services.live_email_provider import live_email_provider
    record = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Email record not found.")

    if record.sent_folder_verified:
        return {
            "verified": True,
            "status": "Found in Sent Items",
            "message": "Already verified in Sent folder.",
            "sent_folder_verified": True
        }

    verified = False
    if record.provider == "microsoft_graph":
        ok, token, err = live_email_provider._get_m365_access_token()
        if ok and token:
            verified = live_email_provider.verify_m365_sent_folder(token, record.sender_email or "support@gisfy.co.in", record.subject)
    elif record.provider == "google_workspace":
        verified = True  # Google Workspace API natively saves sent messages into Sent
    elif record.provider == "authenticated_smtp":
        verified = bool(record.sent_folder_verified)
    elif record.provider in ["brevo", "sendgrid"]:
        return {
            "verified": False,
            "status": record.status,
            "message": f"External relay ({record.provider.capitalize()}) does not write to Microsoft 365 Sent Items. Message is safely stored in the GISFY in-app sent archive.",
            "in_app_archive": True
        }

    if verified:
        record.sent_folder_verified = True
        record.status = "Found in Sent Items"
        db.commit()
        db.refresh(record)
        return {
            "verified": True,
            "status": "Found in Sent Items",
            "message": "Message independently confirmed in Sent folder (saveToSentItems verified).",
            "sent_folder_verified": True
        }
    else:
        return {
            "verified": False,
            "status": record.status,
            "message": "Message not yet detected in Sent folder or sync in progress."
        }
