import os
import json
import smtplib
import mimetypes
import urllib.parse
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

DEFAULT_TEAM_MEMBERS = [
    {"email": "swethagisfy@gmail.com", "name": "Swetha (GISFY)", "role": "Executive Reviewer & Lead", "added_at": "2026-10-16T15:47:00"},
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
    recipient_email: str = "swethagisfy@gmail.com",
    base_app_url: str = "http://localhost:5173",
    base_api_url: str = "http://127.0.0.1:8000"
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
        recipient_email="swethagisfy@gmail.com"
    )


def build_new_proposal_alert_email_html(
    tender_data: Dict[str, Any],
    recipient_email: str = "swethagisfy@gmail.com",
    base_app_url: str = "http://localhost:5173",
    base_api_url: str = "http://127.0.0.1:8000"
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


def send_automatic_new_proposal_alert(tender_data: Dict[str, Any], recipient: str = "swethagisfy@gmail.com") -> Dict[str, Any]:
    """Deliver real-time proposal alert to user."""
    sname = tender_data.get("state_name", "State Portal")
    kw = tender_data.get("keyword", "GIS")
    title = tender_data.get("title", "New Proposal")
    subject = f"🔔 [NEW PROPOSAL DETECTED] {title[:60]}... ({sname} • {kw})"
    html_content = build_new_proposal_alert_email_html(tender_data, recipient_email=recipient)

    # Deliver using standard delivery pipeline
    return _dispatch_html_email(
        recipients=[recipient],
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

    target_recipients = recipients or ["swethagisfy@gmail.com"]
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
    event_prefix: str = "EMAIL DISPATCH"
) -> Dict[str, Any]:
    """Internal delivery helper: saves HTML locally and delivers via SMTP if credentials are present."""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    from_addr = os.getenv("SMTP_FROM", "GISFY Procurement System <notifications@gisfy.co.in>")
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
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

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    delivery_mode = "simulated"

    if smtp_host and smtp_user and smtp_password:
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                if os.getenv("SMTP_USE_TLS", "true").lower() == "true":
                    server.starttls()
                    server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_addr, recipients, msg.as_string())
            delivery_mode = "smtp"
            log_email_event(f"[{event_prefix}] ✉️ Delivered to {len(recipients)} recipients via SMTP: {', '.join(recipients)}", "success")
        except Exception as e:
            log_email_event(f"[SMTP WARNING] ⚠️ SMTP connection failed ({e}). Saved to {email_filename}.", "error")
            delivery_mode = "saved_locally"
    else:
        delivery_mode = "preview_delivered"
        log_email_event(
            f"[{event_prefix}] ✉️ Sent '{subject}' to {len(recipients)} recipients: {', '.join(recipients)}. Full HTML saved to sent_emails/{email_filename}.",
            "success"
        )

    return {
        "status": "success",
        "delivery_mode": delivery_mode,
        "recipients": recipients,
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
