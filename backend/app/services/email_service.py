import os
import json
import smtplib
import mimetypes
import urllib.parse
import base64
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any

from app.db.database import SessionLocal
from app.models import models

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEAM_MEMBERS_FILE = BASE_DIR / "team_members.json"
SENT_EMAILS_DIR = BASE_DIR / "storage" / "sent_emails"
LOG_FILE = BASE_DIR / "scraper.log"


def get_gisfy_logo_base64() -> str:
    """Retrieve GISFY corporate logo as base64 data URI for embedding in HTML emails."""
    candidates = [
        BASE_DIR / "storage" / "gisfy_logo.png",
        BASE_DIR.parent / "frontend" / "public" / "gisfy_logo.png",
        BASE_DIR.parent / "frontend" / "src" / "assets" / "gisfy_logo.png",
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "rb") as lf:
                    b64 = base64.b64encode(lf.read()).decode("utf-8")
                    return f"data:image/png;base64,{b64}"
            except Exception:
                pass
    return "http://127.0.0.1:7035/api/collaboration/gisfy_logo.png"

DEFAULT_TEAM_MEMBERS = [
    {"email": "support@gisfy.co.in", "name": "GISFY Support Team", "role": "ADB Support & Multilateral Outreach", "added_at": "2026-10-24T21:42:00"},
    {"email": "farhath@gisfy.co.in", "name": "Farhath (GISFY ADB Partnerships)", "role": "International Alliances & ADB Operations", "added_at": "2026-10-28T10:00:00"},
    {"email": "firza@gisfy.co.in", "name": "Firza (GISFY Multilateral Lead)", "role": "Multilateral Proposals & Strategic JV Lead", "added_at": "2026-10-28T10:00:00"},
    {"email": "bidding@gisfy.co.in", "name": "GISFY Bidding Operations", "role": "Proposals & Bidding Ops", "added_at": "2026-10-23T15:00:00"},
    {"email": "bidding.gisfy@gmail.com", "name": "GISFY Bidding Operations", "role": "State Outreach & Operations", "added_at": "2026-10-16T15:47:00"},
    {"email": "proposals-team@gisfy.co.in", "name": "GISFY Proposals Team", "role": "Bidding Team", "added_at": "2026-10-15T12:00:00"},
    {"email": "tenders@gisfy.co.in", "name": "GISFY Tender Ops", "role": "Procurement Lead", "added_at": "2026-10-15T12:00:00"},
    {"email": "director.projects@gisfy.co.in", "name": "Project Director", "role": "Executive Review", "added_at": "2026-10-15T12:00:00"}
]


def format_dmy(val: Any) -> str:
    """Format a date or date string to Date, Month, Year format: e.g. '19 Oct 2026'."""
    if not val:
        return "-"
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            try:
                val = datetime.strptime(val[:10], "%Y-%m-%d")
            except Exception:
                return val
    if hasattr(val, "strftime"):
        return val.strftime("%d %b %Y")
    return str(val)


def log_email_event(message: str, typ: str = "success"):
    """Log an email event to scraper.log for real-time Agent Terminal streaming."""
    timestamp = datetime.now().strftime("%d %b %Y %H:%M:%S")
    prefix = "✅" if typ == "success" else ("🚀" if typ == "info" else ("❌" if typ == "error" else "✉️"))
    log_line = f"[{timestamp}] {prefix} {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Failed to log email event: {e}")


def get_team_members() -> List[Dict[str, Any]]:
    """Retrieve list of registered team members."""
    if not TEAM_MEMBERS_FILE.exists():
        save_team_members(DEFAULT_TEAM_MEMBERS)
        return DEFAULT_TEAM_MEMBERS
    try:
        with open(TEAM_MEMBERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_TEAM_MEMBERS


def save_team_members(members: List[Dict[str, Any]]) -> None:
    """Save team members list to JSON file."""
    try:
        with open(TEAM_MEMBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(members, f, indent=2)
    except Exception as e:
        print(f"Error saving team members: {e}")


def add_team_member(email: str, name: Optional[str] = None, role: Optional[str] = "Team Member") -> List[Dict[str, Any]]:
    """Add a new team member recipient."""
    members = get_team_members()
    clean_email = email.strip().lower()
    if not any(m["email"].lower() == clean_email for m in members):
        members.append({
            "email": clean_email,
            "name": name or clean_email.split("@")[0].replace(".", " ").title(),
            "role": role or "Team Member",
            "added_at": datetime.utcnow().isoformat()
        })
        save_team_members(members)
        log_email_event(f"[TEAM RECIPIENT ADDED] 👤 Added team member: {clean_email} ({role})", "info")
    return members


def remove_team_member(email: str) -> List[Dict[str, Any]]:
    """Remove a team member recipient."""
    members = get_team_members()
    clean_email = email.strip().lower()
    updated = [m for m in members if m["email"].lower() != clean_email]
    save_team_members(updated)
    log_email_event(f"[TEAM RECIPIENT REMOVED] 🗑️ Removed team member: {clean_email}", "info")
    return updated


def build_state_keyword_digest_email_html(
    report_data: List[Dict[str, Any]],
    custom_notes: Optional[str] = None,
    recipient_email: str = "bidding.gisfy@gmail.com",
    base_app_url: str = "http://localhost:5173",
    base_api_url: str = "http://127.0.0.1:7035"
) -> str:
    """
    Generate an executive-level, responsive HTML email report organized by State and Keyword.
    Includes direct deep-links to each state and keyword in the web application,
    as well as direct one-click document and PDF download links.
    """
    now_str = datetime.now().strftime("%A, %d %B %Y • %I:%M %p")
    total_states = len(report_data)
    total_proposals = sum(sum(len(k.get("tenders", [])) for k in s.get("keywords", [])) for s in report_data)
    total_docs = sum(s.get("total_docs_count", 0) for s in report_data)

    active_states = []
    for s in report_data:
        kws_with_tenders = [k for k in s.get("keywords", []) if k.get("tenders")]
        if kws_with_tenders:
            active_states.append((s, kws_with_tenders))

    # Quick Jump State Navigation Links
    state_pills_html = ""
    for s, _ in active_states[:12]:
        sname = s["state_name"]
        s_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}"
        state_pills_html += f"""
        <a href="{s_link}" style="display: inline-block; margin: 3px 4px; padding: 5px 12px; background: #e0e7ff; color: #4338ca; text-decoration: none; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #c7d2fe;">
            🏛️ {sname}
        </a>
        """

    # Build States & Keywords HTML
    states_content_html = ""
    for s, kws in active_states[:12]:
        sname = s["state_name"]
        portal_url = s.get("portal_url") or "https://eprocure.gov.in"
        state_app_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}"
        state_tender_count = sum(len(k["tenders"]) for k in kws)

        keywords_html = ""
        for kw_obj in kws:
            kw_name = kw_obj["keyword"]
            tenders = kw_obj["tenders"]
            kw_app_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}&keyword={urllib.parse.quote(kw_name)}"

            tenders_html = ""
            for t in tenders[:6]:
                tid = t.get("tender_id")
                tender_app_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}&keyword={urllib.parse.quote(kw_name)}&tender={tid}"

                docs = t.get("documents", [])
                docs_rows_html = ""
                for d in docs:
                    fname = d.get("file_name", "Document")
                    fsize = f"{d.get('file_size_kb', 0)} KB" if d.get('file_size_kb') else "Ready"
                    is_zip = d.get("file_type") == ".zip" or fname.endswith(".zip") or d.get("is_bundle")
                    
                    sub_count = len(d.get("sub_documents", []))
                    sub_docs = d.get("sub_documents", [])

                    doc_id_param = f"id={d.get('id', '')}" if (d.get('id') and d.get('id') < 800000) else f"path={urllib.parse.quote(d.get('local_path') or '')}"
                    dl_url = f"{base_api_url}/api/documents/download?{doc_id_param}&attachment=true"

                    badge_bg = "#fef3c7" if is_zip else ("#eff6ff" if fname.lower().endswith(".pdf") else "#ecfdf5")
                    badge_color = "#92400e" if is_zip else ("#1d4ed8" if fname.lower().endswith(".pdf") else "#047857")
                    badge_label = "📦 ZIP ARCHIVE" if is_zip else ("📕 PDF" if fname.lower().endswith(".pdf") else "📊 BOQ / DATA")

                    sub_items_html = ""
                    if sub_count > 0:
                        sub_rows = ""
                        for sub_d in sub_docs[:5]:
                            sub_fname = sub_d.get("file_name")
                            sub_id_param = f"id={sub_d.get('id', '')}" if (sub_d.get('id') and sub_d.get('id') < 800000) else f"path={urllib.parse.quote(sub_d.get('local_path') or '')}"
                            sub_dl = f"{base_api_url}/api/documents/download?{sub_id_param}&attachment=true"
                            sub_rows += f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; border-bottom: 1px solid #f1f5f9; font-size: 11px;">
                                <span style="color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 420px;">📄 {sub_fname}</span>
                                <a href="{sub_dl}" style="color: #4f46e5; text-decoration: none; font-weight: 600; margin-left: 8px;">⬇ Download</a>
                            </div>
                            """
                        more_sub_text = f"<div style='font-size: 11px; color: #64748b; padding: 4px 8px;'>... plus {sub_count - 5} more sections viewable in portal</div>" if sub_count > 5 else ""
                        sub_items_html = f"""
                        <div style="background: #f8fafc; border-left: 3px solid #6366f1; margin: 6px 0 10px 16px; padding: 6px 10px; border-radius: 4px;">
                            <div style="font-size: 11px; font-weight: 700; color: #4338ca; margin-bottom: 4px;">📂 Extracted Sections from {fname} ({sub_count} files):</div>
                            {sub_rows}
                            {more_sub_text}
                        </div>
                        """

                    docs_rows_html += f"""
                    <div style="padding: 8px 12px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; background: {badge_bg}; color: {badge_color}; margin-right: 6px;">
                                {badge_label}
                            </span>
                            <span style="font-size: 12px; font-weight: 600; color: #1e293b;">{fname}</span>
                            <span style="font-size: 11px; color: #64748b; margin-left: 6px;">({fsize})</span>
                        </div>
                        <div>
                            <a href="{dl_url}" style="display: inline-block; padding: 4px 10px; background: #6366f1; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 11px; font-weight: 600;">
                                ⬇ Download
                            </a>
                        </div>
                    </div>
                    {sub_items_html}
                    """

                stage_badge = (
                    '<span style="background: #ecfdf5; color: #047857; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 10px;">🟢 LIVE ACTIVE</span>'
                    if t.get("is_live") else
                    ('<span style="background: #eff6ff; color: #1d4ed8; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 10px;">⏳ UPCOMING</span>'
                     if t.get("is_upcoming") else
                     '<span style="background: #fef2f2; color: #b91c1c; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 10px;">⚠️ CLOSING SOON</span>')
                )

                tenders_html += f"""
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                            <span style="font-size: 11px; font-weight: 700; background: #f1f5f9; padding: 2px 8px; border-radius: 6px; color: #334155;">
                                REF #{tid}
                            </span>
                            <span style="margin-left: 6px;">{stage_badge}</span>
                        </div>
                        <a href="{tender_app_link}" style="display: inline-block; padding: 3px 10px; background: #4f46e5; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 11px; font-weight: 600;">
                            🚀 Open Proposal in App ↗
                        </a>
                    </div>
                    
                    <h4 style="margin: 0 0 6px 0; font-size: 14px; color: #0f172a; line-height: 1.4;">
                        {t.get('title')}
                    </h4>
                    
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 10px;">
                        🏛️ <i>{t.get('department', 'State Directorate')}</i>
                        {f" • 📅 Published: {format_dmy(t.get('published_date'))}" if t.get('published_date') else ""}
                        {f" • <span style='color: #dc2626; font-weight: 600;'>⏰ Due Date: {format_dmy(t.get('last_date'))}</span>" if t.get('last_date') else ""}
                        {f" • <a href='{t.get('portal_tender_url')}' style='color: #2563eb; text-decoration: none;'>Official Notice ↗</a>" if t.get('portal_tender_url') else ""}
                    </div>
                    
                    <!-- Attached Documents Card -->
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
                        <div style="padding: 6px 12px; background: #eef2ff; font-size: 11px; font-weight: 700; color: #4338ca;">
                            ATTACHED PROPOSAL DOCUMENTS ({len(docs)} portal packages):
                        </div>
                        {docs_rows_html}
                    </div>
                </div>
                """

            keywords_html += f"""
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 6px 10px; background: #f1f5f9; border-radius: 8px; border-left: 4px solid #4f46e5;">
                    <span style="font-size: 13px; font-weight: 700; color: #1e293b;">
                        🏷️ Keyword: <span style="color: #4f46e5;">{kw_name}</span> ({len(tenders)} Proposals)
                    </span>
                    <a href="{kw_app_link}" style="color: #4f46e5; text-decoration: none; font-size: 12px; font-weight: 600;">
                        🔗 View {sname} · {kw_name} Link ↗
                    </a>
                </div>
                {tenders_html}
            </div>
            """

        states_content_html += f"""
        <div style="background: #ffffff; border: 2px solid #e2e8f0; border-radius: 14px; padding: 20px; margin-bottom: 28px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; margin-bottom: 16px; border-bottom: 2px solid #f1f5f9;">
                <div>
                    <h2 style="margin: 0; font-size: 18px; color: #0f172a; font-weight: 800;">
                        🏛️ {sname}
                    </h2>
                    <span style="font-size: 12px; color: #64748b;">
                        {state_tender_count} Targeted Proposals Across Keywords • <a href="{portal_url}" style="color: #2563eb; text-decoration: none;">Portal Link ↗</a>
                    </span>
                </div>
                <a href="{state_app_link}" style="display: inline-block; padding: 6px 14px; background: #059669; color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 12px; font-weight: 700;">
                    🌐 Open {sname} in Portal ↗
                </a>
            </div>
            {keywords_html}
        </div>
        """

    custom_notes_html = f"""
    <div style="background: #fefce8; border: 1px solid #fef08a; border-radius: 10px; padding: 14px 18px; margin-bottom: 24px; color: #713f12; font-size: 13px; line-height: 1.5;">
        <b>📝 Team Dispatch Notes:</b><br/>
        {custom_notes}
    </div>
    """ if custom_notes else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GISFY State &amp; Keyword Proposals Report</title>
    </head>
    <body style="margin: 0; padding: 0; background: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8fafc; padding: 25px 10px;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 820px; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">
                        <!-- Header Banner -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4f46e5 100%); padding: 32px 36px; color: #ffffff;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <span style="font-size: 17px; font-weight: 800; letter-spacing: 1px; color: #38bdf8; text-transform: uppercase;">
                                        GISFY <span style="color: #ffffff; font-weight: 400;">PROPOSAL INTELLIGENCE</span>
                                    </span>
                                    <span style="background: rgba(255,255,255,0.18); padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #ffffff;">
                                        STATE &amp; KEYWORD DISPATCH
                                    </span>
                                </div>
                                <h1 style="margin: 0 0 10px 0; font-size: 23px; font-weight: 800; color: #ffffff; line-height: 1.3;">
                                    Executive Procurement Report &amp; Attached Documents
                                </h1>
                                <p style="margin: 0; font-size: 13px; opacity: 0.9; color: #e0e7ff;">
                                    Prepared for: <b>{recipient_email}</b> • Generated: {now_str}
                                </p>
                            </td>
                        </tr>

                        <!-- Quick Summary Stats -->
                        <tr>
                            <td style="padding: 24px 36px 0 36px;">
                                {custom_notes_html}
                                <!-- Master Excel Spreadsheet Banner -->
                                <div style="background: linear-gradient(135deg, #065f46 0%, #047857 50%, #059669 100%); color: #ffffff; border-radius: 12px; padding: 20px 24px; margin-bottom: 22px; box-shadow: 0 4px 14px rgba(4,120,87,0.2);">
                                    <div style="font-size: 11px; font-weight: 800; letter-spacing: 1px; color: #a7f3d0; text-transform: uppercase; margin-bottom: 6px;">
                                        📊 MASTER EXCEL SPREADSHEET &amp; DOCUMENT REPOSITORY
                                    </div>
                                    <h3 style="margin: 0 0 8px 0; font-size: 17px; font-weight: 800; color: #ffffff;">
                                        All States, Keywords &amp; Downloadable Documents in One Excel File
                                    </h3>
                                    <p style="margin: 0 0 16px 0; font-size: 13px; color: #d1fae5; line-height: 1.45;">
                                        Click below to open the interactive spreadsheet view or download the Excel (.xlsx) file with direct one-click download links for every attached tender PDF, BOQ, and zip archive.
                                    </p>
                                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                                        <a href="{base_api_url}/api/reports/excel-view" style="display: inline-block; padding: 9px 18px; background: rgba(255,255,255,0.22); border: 1px solid rgba(255,255,255,0.4); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 12px; font-weight: 700;">
                                            🖥️ Open Spreadsheet Grid View ↗
                                        </a>
                                        <a href="{base_api_url}/api/reports/proposals-excel" style="display: inline-block; padding: 9px 20px; background: #ffffff; color: #065f46; text-decoration: none; border-radius: 8px; font-size: 12px; font-weight: 800; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
                                            📥 Download Excel File (.xlsx)
                                        </a>
                                    </div>
                                </div>

                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                    <tr>
                                        <td style="width: 33%; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; text-align: center;">
                                            <div style="font-size: 22px; font-weight: 800; color: #4f46e5;">{total_states}</div>
                                            <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; margin-top: 4px;">States Monitored</div>
                                        </td>
                                        <td style="width: 33%; padding: 12px; background: #ecfdf5; border: 1px solid #bbf7d0; border-radius: 10px; text-align: center;">
                                            <div style="font-size: 22px; font-weight: 800; color: #047857;">{total_proposals}</div>
                                            <div style="font-size: 11px; font-weight: 600; color: #065f46; text-transform: uppercase; margin-top: 4px;">Active Proposals</div>
                                        </td>
                                        <td style="width: 33%; padding: 12px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; text-align: center;">
                                            <div style="font-size: 22px; font-weight: 800; color: #1d4ed8;">{total_docs}</div>
                                            <div style="font-size: 11px; font-weight: 600; color: #1e40af; text-transform: uppercase; margin-top: 4px;">Proposal Documents</div>
                                        </td>
                                    </tr>
                                </table>

                                <!-- Quick State Jump Links -->
                                <div style="background: #f1f5f9; border-radius: 10px; padding: 12px 14px; margin-bottom: 24px;">
                                    <div style="font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px;">
                                        ⚡ QUICK JUMP TO STATE (Click to open in app):
                                    </div>
                                    <div>
                                        {state_pills_html}
                                    </div>
                                </div>
                            </td>
                        </tr>

                        <!-- States & Keywords Content -->
                        <tr>
                            <td style="padding: 0 36px 30px 36px;">
                                {states_content_html}

                                <!-- Portal Action Banner -->
                                <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); color: #ffffff; border-radius: 12px; padding: 22px; text-align: center; margin-top: 20px;">
                                    <h3 style="margin: 0 0 8px 0; font-size: 17px; font-weight: 800;">🚀 Open GISFY Automated Proposals Web Application</h3>
                                    <p style="margin: 0 0 14px 0; font-size: 13px; opacity: 0.95;">
                                        Interactive state navigation, keyword filtering, and authentic document previewing are active.
                                    </p>
                                    <a href="{base_app_url}" style="display: inline-block; background: #ffffff; color: #047857; text-decoration: none; padding: 11px 26px; border-radius: 8px; font-weight: 800; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                                        Launch Full Web Portal ↗
                                    </a>
                                </div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 22px 36px; text-align: center; font-size: 12px; color: #94a3b8; line-height: 1.6;">
                                <p style="margin: 0 0 4px 0; font-weight: 600; color: #64748b;">
                                    GISFY Agentic Procurement Intelligence System • Automated Proposals
                                </p>
                                <p style="margin: 0;">
                                    Delivered to: <b>{recipient_email}</b> • Confidential &amp; Proprietary
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


def build_state_email_html(
    state_name: Optional[str] = None,
    tenders_data: Optional[List[Dict[str, Any]]] = None,
    state_obj: Any = None,
    custom_notes: Optional[str] = None,
    include_all_states: bool = False
) -> str:
    """Preview helper that constructs state-keyword HTML report."""
    from app.routers.reports import get_state_keyword_report
    db = SessionLocal()
    try:
        report_data = get_state_keyword_report(db)
        if state_name and not include_all_states:
            report_data = [s for s in report_data if s["state_name"].lower() == state_name.lower()]
    finally:
        db.close()

    return build_state_keyword_digest_email_html(
        report_data=report_data,
        custom_notes=custom_notes,
        recipient_email="bidding.gisfy@gmail.com"
    )


def build_new_proposal_alert_email_html(
    tender_data: Dict[str, Any],
    recipient_email: str = "bidding.gisfy@gmail.com",
    base_app_url: str = "http://localhost:5173",
    base_api_url: str = "http://127.0.0.1:7035"
) -> str:
    """Generate high-priority alert email when a new proposal is detected on any state portal."""
    now_str = datetime.now().strftime("%A, %d %B %Y • %I:%M %p")
    tid = tender_data.get("tender_id")
    sname = tender_data.get("state_name", "Government Portal")
    kw = tender_data.get("keyword", "GIS")
    title = tender_data.get("title", "New Proposal")
    dept = tender_data.get("department", "State Directorate")
    due_date = tender_data.get("last_date") or tender_data.get("due_date") or "Check Portal"
    portal_url = tender_data.get("portal_url") or "https://eprocure.gov.in"

    app_deep_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}&keyword={urllib.parse.quote(kw)}&tender={tid}"
    kw_deep_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}&keyword={urllib.parse.quote(kw)}"
    state_deep_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}"

    docs = tender_data.get("documents", [])
    docs_rows_html = ""
    for d in docs:
        fname = d.get("file_name", "Document")
        fsize = f"{d.get('file_size_kb', 0)} KB" if d.get('file_size_kb') else "Ready"
        is_zip = fname.lower().endswith(".zip")
        doc_id_param = f"id={d.get('id', '')}" if (d.get('id') and d.get('id') < 800000) else f"path={urllib.parse.quote(d.get('local_path') or '')}"
        dl_url = f"{base_api_url}/api/documents/download?{doc_id_param}&attachment=true"

        docs_rows_html += f"""
        <div style="padding: 8px 12px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 12px; font-weight: 600; color: #1e293b;">📄 {fname}</span>
                <span style="font-size: 11px; color: #64748b; margin-left: 6px;">({fsize})</span>
            </div>
            <a href="{dl_url}" style="display: inline-block; padding: 4px 10px; background: #6366f1; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 11px; font-weight: 600;">
                ⬇ Download
            </a>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>New Proposal Alert</title></head>
    <body style="margin: 0; padding: 0; background: #fef2f2; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding: 25px 10px;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 720px; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.06); border: 2px solid #fecaca;">
                        <tr>
                            <td style="background: linear-gradient(135deg, #b91c1c 0%, #dc2626 50%, #ea580c 100%); padding: 30px 35px; color: #ffffff;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 13px; font-weight: 800; letter-spacing: 1px; color: #ffffff; text-transform: uppercase;">
                                        🚨 REAL-TIME NEW PROPOSAL DETECTED
                                    </span>
                                    <span style="background: rgba(255,255,255,0.25); padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;">
                                        {sname} • {kw}
                                    </span>
                                </div>
                                <h1 style="margin: 0 0 6px 0; font-size: 21px; font-weight: 800; line-height: 1.3;">
                                    {title}
                                </h1>
                                <p style="margin: 0; font-size: 12px; opacity: 0.9;">
                                    Detected: {now_str} • Delivered to: <b>{recipient_email}</b>
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 26px 35px;">
                                <div style="display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap;">
                                    <a href="{state_deep_link}" style="padding: 6px 12px; background: #f1f5f9; color: #334155; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600;">
                                        🏛️ State: <b>{sname}</b> ↗
                                    </a>
                                    <a href="{kw_deep_link}" style="padding: 6px 12px; background: #e0e7ff; color: #4338ca; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 600;">
                                        🏷️ Keyword: <b>{kw}</b> ↗
                                    </a>
                                    <span style="padding: 6px 12px; background: #fef2f2; color: #dc2626; border-radius: 8px; font-size: 12px; font-weight: 600;">
                                        ⏰ Due: <b>{format_dmy(due_date)}</b>
                                    </span>
                                </div>

                                <div style="font-size: 13px; color: #475569; margin-bottom: 16px;">
                                    <b>Department:</b> {dept} • <b>Reference Number:</b> #{tid}
                                </div>

                                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 22px;">
                                    <div style="padding: 8px 12px; background: #fee2e2; font-size: 12px; font-weight: 700; color: #991b1b;">
                                        ATTACHED AUTHENTIC PROPOSAL DOCUMENTS ({len(docs)} files):
                                    </div>
                                    {docs_rows_html if docs_rows_html else "<div style='padding: 10px; font-size: 12px; color: #64748b;'>Attached files ready on official portal</div>"}
                                </div>

                                <div style="text-align: center; margin-top: 15px;">
                                    <a href="{app_deep_link}" style="display: inline-block; padding: 12px 28px; background: #dc2626; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 800; font-size: 14px; box-shadow: 0 4px 12px rgba(220,38,38,0.25);">
                                        🚀 Open &amp; Review Proposal in GISFY App ↗
                                    </a>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def send_automatic_new_proposal_alert(tender_data: Dict[str, Any], recipient: Optional[str] = None) -> Dict[str, Any]:
    """Deliver real-time proposal alert to registered team members."""
    team_members = get_team_members()
    recipients = []
    if recipient:
        recipients.append(recipient.strip())
    for m in team_members:
        em = m.get("email", "").strip()
        if em and em.lower() not in [r.lower() for r in recipients]:
            recipients.append(em)
    if not recipients:
        recipients = ["bidding.gisfy@gmail.com"]

    sname = tender_data.get("state_name", "State Portal")
    kw = tender_data.get("keyword", "GIS")
    title = tender_data.get("title", "New Proposal")
    subject = f"🔔 [NEW PROPOSAL DETECTED] {title[:60]}... ({sname} • {kw})"
    html_content = build_new_proposal_alert_email_html(tender_data, recipient_email=", ".join(recipients))

    # Deliver using standard delivery pipeline
    return _dispatch_html_email(
        recipients=recipients,
        subject=subject,
        html_content=html_content,
        state_name=sname,
        tender_id=tender_data.get("tender_id"),
        event_prefix="NEW PROPOSAL ALERT"
    )


def send_state_keyword_digest(
    recipients: Optional[List[str]] = None,
    custom_notes: Optional[str] = None
) -> Dict[str, Any]:
    """Generate and dispatch comprehensive State & Keyword email report."""
    from app.routers.reports import get_state_keyword_report
    db = SessionLocal()
    try:
        report_data = get_state_keyword_report(db)
    finally:
        db.close()

    team_members = get_team_members()
    target_recipients = recipients or [m["email"] for m in team_members if m.get("email")]
    if not target_recipients:
        target_recipients = ["bidding.gisfy@gmail.com"]

    subject = "[GISFY Proposal Intelligence] Executive State & Keyword Procurement Report with Downloadable Documents"
    html_content = build_state_keyword_digest_email_html(
        report_data=report_data,
        custom_notes=custom_notes,
        recipient_email=", ".join(target_recipients)
    )

    return _dispatch_html_email(
        recipients=target_recipients,
        subject=subject,
        html_content=html_content,
        state_name="All 29 States",
        event_prefix="STATE & KEYWORD DIGEST"
    )


def _dispatch_html_email(
    recipients: List[str],
    subject: str,
    html_content: str,
    state_name: Optional[str] = None,
    tender_id: Optional[str] = None,
    event_prefix: str = "EMAIL DISPATCH",
    from_address: Optional[str] = None,
    cc_recipients: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Internal delivery helper: saves HTML locally and delivers via SMTP if credentials are present."""
    reload_smtp_env()
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_addr = from_address or os.getenv("SMTP_FROM") or (f"GISFY Support <{smtp_user}>" if smtp_user else "GISFY Support <support@gisfy.co.in>")

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    if cc_recipients:
        msg["Cc"] = ", ".join(cc_recipients)
    msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    # Attach Master Excel Spreadsheet (.xlsx)
    try:
        from app.services.excel_service import generate_proposals_excel
        excel_path = generate_proposals_excel()
        if excel_path and excel_path.exists():
            with open(excel_path, "rb") as ef:
                excel_part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                excel_part.set_payload(ef.read())
            encoders.encode_base64(excel_part)
            excel_part.add_header(
                "Content-Disposition",
                'attachment',
                filename="GISFY_Proposals_And_Documents_Master.xlsx"
            )
            msg.attach(excel_part)
    except Exception as exc:
        print(f"Notice: Excel attachment skipped: {exc}")

    SENT_EMAILS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_subj = "".join(c for c in subject if c.isalnum() or c in (" ", "-", "_")).strip()[:40].replace(" ", "_")
    email_filename = f"{timestamp_slug}_{clean_subj}.html"
    email_file_path = SENT_EMAILS_DIR / email_filename

    with open(email_file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    delivery_mode = "simulated"
    smtp_error = None

    # Merge all targets for actual SMTP delivery envelope
    all_send_recipients = list(dict.fromkeys([r.strip() for r in (recipients + (cc_recipients or [])) if r and "@" in r]))

    if smtp_host and smtp_user and smtp_password:
        try:
            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_addr, all_send_recipients, msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    server.ehlo()
                    if os.getenv("SMTP_USE_TLS", "true").lower() == "true":
                        server.starttls()
                        server.ehlo()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_addr, all_send_recipients, msg.as_string())
            delivery_mode = "smtp"
            cc_str = f" (CC: {', '.join(cc_recipients)})" if cc_recipients else ""
            log_email_event(f"[{event_prefix}] ✉️ Delivered to {len(recipients)} recipients via SMTP: {', '.join(recipients)}{cc_str}", "success")
        except Exception as e:
            smtp_error = str(e)
            log_email_event(f"[SMTP WARNING] ⚠️ SMTP connection failed ({e}). Saved to {email_filename}.", "error")
            delivery_mode = "saved_locally"
    else:
        delivery_mode = "preview_delivered"
        cc_str = f" (CC: {', '.join(cc_recipients)})" if cc_recipients else ""
        log_email_event(
            f"[{event_prefix}] ✉️ Sent '{subject}' to {len(recipients)} recipients: {', '.join(recipients)}{cc_str}. Full HTML saved to sent_emails/{email_filename}.",
            "success"
        )

    is_error = bool(smtp_error)
    return {
        "status": "error" if is_error else "success",
        "delivery_mode": delivery_mode,
        "message": f"SMTP delivery failed: {smtp_error}. Saved locally to {email_filename}" if smtp_error else ("Saved locally in archive (SMTP not configured)" if delivery_mode == "preview_delivered" else "Delivered via SMTP"),
        "error": smtp_error,
        "from_address": from_addr,
        "recipients": recipients,
        "cc_recipients": cc_recipients or [],
        "subject": subject,
        "state_name": state_name or "Official Portals",
        "tender_id": tender_id,
        "sent_at": datetime.utcnow().isoformat(),
        "preview_file": email_filename,
        "view_url": f"/api/email/view/{email_filename}"
    }


def send_email_dispatch(
    recipients: List[str],
    subject: str,
    state_name: Optional[str] = None,
    tender_id: Optional[str] = None,
    include_all_states: bool = False,
    attach_zip_bundle: bool = True,
    custom_notes: Optional[str] = None
) -> Dict[str, Any]:
    """Main dispatch router endpoint."""
    if include_all_states:
        return send_state_keyword_digest(recipients=recipients, custom_notes=custom_notes)

    from app.routers.reports import get_state_keyword_report
    db = SessionLocal()
    try:
        report_data = get_state_keyword_report(db)
        if state_name:
            report_data = [s for s in report_data if s["state_name"].lower() == state_name.lower()]
    finally:
        db.close()

    html_content = build_state_keyword_digest_email_html(
        report_data=report_data,
        custom_notes=custom_notes,
        recipient_email=", ".join(recipients)
    )

    return _dispatch_html_email(
        recipients=recipients,
        subject=subject,
        html_content=html_content,
        state_name=state_name,
        tender_id=tender_id,
        event_prefix="STATE EMAIL DISPATCH"
    )


def reload_smtp_env():
    """Reload SMTP environment variables from backend/.env if modified."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    os.environ[key] = val


def get_smtp_status() -> Dict[str, Any]:
    """Retrieve current SMTP configuration status and delivery mode."""
    reload_smtp_env()
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    is_configured = bool(smtp_host and smtp_user and smtp_password)

    return {
        "is_configured": is_configured,
        "delivery_mode": "smtp" if is_configured else "local_archive",
        "smtp_host": smtp_host or "Not Configured",
        "smtp_port": int(os.getenv("SMTP_PORT", 587)),
        "smtp_user": smtp_user or "None",
        "smtp_from": os.getenv("SMTP_FROM", "GISFY Procurement System <notifications@gisfy.co.in>"),
        "archive_directory": str(SENT_EMAILS_DIR)
    }


def save_smtp_config(
    host: str,
    port: int = 587,
    user: str = "",
    password: str = "",
    from_email: Optional[str] = None,
    use_tls: bool = True
) -> Dict[str, Any]:
    """Save SMTP credentials to backend/.env and update active environment."""
    env_file = BASE_DIR / ".env"
    lines = []
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    # Filter out existing SMTP keys
    smtp_keys = {"SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_USE_TLS"}
    filtered_lines = [l for l in lines if not any(l.strip().startswith(f"{k}=") for k in smtp_keys)]

    from_val = from_email or f"GISFY Procurement System <{user}>"
    new_smtp_block = [
        f"SMTP_HOST={host}\n",
        f"SMTP_PORT={port}\n",
        f"SMTP_USER={user}\n",
        f"SMTP_PASSWORD={password}\n",
        f"SMTP_FROM={from_val}\n",
        f"SMTP_USE_TLS={'true' if use_tls else 'false'}\n"
    ]

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(filtered_lines + ["\n"] + new_smtp_block)

    # Update active os.environ
    os.environ["SMTP_HOST"] = host
    os.environ["SMTP_PORT"] = str(port)
    os.environ["SMTP_USER"] = user
    os.environ["SMTP_PASSWORD"] = password
    os.environ["SMTP_FROM"] = from_val
    os.environ["SMTP_USE_TLS"] = "true" if use_tls else "false"

    log_email_event(f"[SMTP CONFIG] Updated SMTP server settings for {user} ({host}:{port})", "info")
    return get_smtp_status()


def test_smtp_connection(target_email: str = "support@gisfy.co.in") -> Dict[str, Any]:
    """Send an immediate test verification email to target_email."""
    reload_smtp_env()
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    cc_target = os.getenv("SMTP_CC", "").strip()

    if not (smtp_host and smtp_user and smtp_password):
        return {
            "status": "error",
            "message": "SMTP credentials are not configured in backend/.env. Please provide SMTP_USER and SMTP_PASSWORD.",
            "is_configured": False
        }

    test_subject = f"✅ [GISFY SMTP Test] Connection Verified to {target_email}"
    cc_html_line = f"<b>CC:</b> {cc_target}<br/>" if cc_target else ""
    test_html = f"""
    <div style="font-family: sans-serif; padding: 24px; background: #f8fafc; border-radius: 12px; border: 1px solid #e2e8f0; max-width: 600px; margin: auto;">
        <h2 style="color: #4f46e5; margin-top: 0;">🎉 GISFY Email Delivery Online!</h2>
        <p>This is a live verification email from your <b>GISFY Automated Proposals Platform</b> delivered via <b>{smtp_host}:{smtp_port}</b>.</p>
        <div style="background: #ffffff; padding: 14px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 13px;">
            <b>Sender:</b> {os.getenv('SMTP_FROM', smtp_user)}<br/>
            <b>Recipient:</b> {target_email}<br/>
            {cc_html_line}
            <b>Timestamp:</b> {datetime.utcnow().strftime('%d %B %Y, %H:%M:%S UTC')}
        </div>
        <p style="font-size: 12px; color: #64748b; margin-top: 16px;">All automated proposal alerts and joint venture collaboration letters will now arrive directly in your inbox.</p>
    </div>
    """
    res = _dispatch_html_email(
        recipients=[target_email],
        subject=test_subject,
        html_content=test_html,
        cc_recipients=[cc_target] if cc_target else None,
        event_prefix="SMTP VERIFICATION TEST"
    )
    return res


def build_collaboration_email_html(
    tender: Any = None,
    partner: Any = None,
    match_info: Optional[Dict[str, Any]] = None,
    letter_text: Optional[str] = None,
    jv_split: Optional[str] = None,
    custom_notes: Optional[str] = None,
    gisfy_name: str = "N C Harika | Business Development Executive",
    gisfy_email: str = "support@gisfy.co.in",
    cc_email: Optional[str] = None,
    technical_scope_paragraph: Optional[str] = None,
    sector_phrase: Optional[str] = None
) -> str:
    """
    Generate clean executive HTML email for Joint Venture / Consortium Collaboration.
    Strictly includes only the letter from 'Dear Team,' to 'Thanks & Regards,' and the GISFY logo.
    Dynamically generates the 2-sentence technical scope tailored to the project/tender.
    Omits all unnecessary banners, partner cards, why needed boxes, attached document download links, action buttons, and disclaimers.
    """
    from app.services.collaboration_email_service import generate_project_technical_scope, clean_project_title

    logo_src = get_gisfy_logo_base64()
    sender_title = gisfy_name or "N C Harika | Business Development Executive"
    clean_title = clean_project_title(getattr(tender, "title", "") if tender else "")

    if not technical_scope_paragraph:
        title = getattr(tender, "title", "") if tender else ""
        desc = getattr(tender, "description", "") if tender else ""
        dept = getattr(tender, "department", "") if tender else ""
        kw_str = " ".join([k.keyword for k in getattr(tender, "keywords", [])]) if tender and getattr(tender, "keywords", None) else ""
        proj_sec = getattr(getattr(tender, "adb_details", None), "project_sector", None) if tender else None
        scope_work = getattr(getattr(tender, "adb_details", None), "scope_of_work", "") if tender else ""

        technical_scope_paragraph, derived_phrase, _ = generate_project_technical_scope(
            title=title,
            description=desc,
            project_sector=proj_sec or sector_phrase,
            department=dept,
            keywords_str=kw_str,
            scope_of_work=scope_work
        )
        if not sector_phrase:
            sector_phrase = derived_phrase

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exploring JV / Consortium Partnership</title>
</head>
<body style="margin: 0; padding: 16px 20px 36px 20px; background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #1e293b; text-align: left;">
    <div style="margin: 0; padding: 0; max-width: 720px; text-align: left; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; line-height: 1.6; color: #1e293b;">
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">Dear Team,</p>
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">Greetings from GISFY Private Limited, India.</p>
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.</p>
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">We are currently exploring a potential Joint Venture (JV) / Consortium partnership with your organisation to collaborate and work together for the following project:</p>
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">{technical_scope_paragraph}</p>
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">Considering your organisation's expertise and experience, we believe there are strong synergies for mutual collaboration in the joint execution and implementation of this project.</p>
        <p style="margin: 0 0 14px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following preliminary documents for our mutual evaluation:</p>
        <div style="margin: 0 0 16px 0; padding: 0; text-align: left;">
            <p style="margin: 0 0 6px 0; padding: 0; line-height: 1.5; color: #1e293b; text-align: left;">Company Profile – Highlighting technical capabilities, core competencies, and areas of expertise.</p>
            <p style="margin: 0 0 6px 0; padding: 0; line-height: 1.5; color: #1e293b; text-align: left;">Company Registration Certificate – Valid documentation confirming legal registration.</p>
            <p style="margin: 0 0 6px 0; padding: 0; line-height: 1.5; color: #1e293b; text-align: left;">Tax Registration Certificate – Applicable tax registration documents.</p>
            <p style="margin: 0 0 6px 0; padding: 0; line-height: 1.5; color: #1e293b; text-align: left;">CVs of Key Experts – Profiles of qualified professionals and technical specialists.</p>
            <p style="margin: 0 0 6px 0; padding: 0; line-height: 1.5; color: #1e293b; text-align: left;">Relevant Project Experience – Overview of similar completed or ongoing projects.</p>
        </div>
        <p style="margin: 0 0 16px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">Upon receiving and reviewing these details, we would be pleased to schedule an introductory discussion and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.</p>
        <p style="margin: 0 0 24px 0; padding: 0; line-height: 1.6; color: #1e293b; text-align: left;">We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.</p>
        <div style="margin-top: 24px; padding: 0; text-align: left; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <p style="margin: 0 0 12px 0; padding: 0; font-size: 14.5px; font-weight: 500; color: #1e293b; line-height: 1.4; text-align: left;">Thanks &amp; Regards,</p>
            <p style="margin: 0 0 4px 0; padding: 0; font-size: 15px; font-weight: 700; color: #0f172a; line-height: 1.4; text-align: left;">{sender_title}</p>
            <p style="margin: 0 0 14px 0; padding: 0; font-size: 13.5px; color: #475569; line-height: 1.45; text-align: left;">
                GISFY Private Limited, Ground Floor, DSL Abacus IT Park,<br>
                Uppal, Hyderabad, Telangana – 500039, India<br>
                Mobile: +91 90631 20678<br>
                Website : <a href="https://www.gisfy.co.in" target="_blank" style="color: #2563eb; text-decoration: none;">www.gisfy.co.in</a>
            </p>
            <div style="margin: 0 0 24px 0; padding: 0; text-align: left;">
                <img src="{logo_src}" alt="GISFY" width="160" height="39" style="display: block; width: 160px; max-width: 160px; height: auto; border: 0; outline: none; text-decoration: none;" />
            </div>
        </div>
    </div>
</body>
</html>"""


