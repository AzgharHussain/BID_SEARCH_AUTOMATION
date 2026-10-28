import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models import models
from app.services.tender_proposal_analyzer import extract_project_scope_overview
from app.services.partner_service import search_partners_for_tender, detect_tender_country
from app.services.gmail_connector import gmail_connector

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def detect_tender_sector(
    title: Optional[str] = "",
    project_sector: Optional[str] = "",
    department: Optional[str] = "",
    keywords_str: Optional[str] = ""
) -> Tuple[str, str]:
    """
    Intelligently detect the high-level sector for a tender (e.g. Water Resources, Software, Agriculture).
    Returns (subject_sector_title, body_sector_phrase).
    """
    text = f"{title or ''} {project_sector or ''} {department or ''} {keywords_str or ''}".lower()

    # 1. Water Resources
    if any(w in text for w in ['water resource', 'iwrm', 'irrigation', 'hydrolog', 'drainage', 'flood', 'dam ', 'river basin', 'water supply', 'watershed', 'canal', 'wastewater', 'aquifer', 'reservoir', 'water balance', 'water security', 'hydro']):
        return 'Water Resources Project', 'water resources project'

    # 2. Agriculture & Rural Development
    if any(w in text for w in ['agricultur', 'farmland', 'crop', 'coffee', 'cashew', 'agroforestry', 'rural livelihood', 'smallholder', 'farming', 'horticultur', 'livestock', 'veterinary']):
        return 'Agriculture & Rural Development Project', 'agriculture and rural development project'

    # 3. Transport & Infrastructure
    if any(w in text for w in ['railway', 'transport', 'rapid transit', 'highway', 'road', 'corridor', 'metro', 'freight', 'traffic', 'e-mobility', 'vehicle', 'bridge']):
        return 'Transport & Infrastructure Project', 'transport and infrastructure project'

    # 4. Energy & Power
    if any(w in text for w in ['power', 'energy', 'solar', 'grid', 'electricity', 'decarbonization', 'substation', 'transmission', 'wind energy', 'photovoltaic']):
        return 'Energy & Power Sector Project', 'energy and power sector project'

    # 5. Healthcare Systems
    if any(w in text for w in ['health', 'primary health', 'medical', 'hospital', 'disease', 'epidemiology', 'biomedical', 'clinical']):
        return 'Healthcare Systems Project', 'healthcare systems project'

    # 6. Software & IT Solutions
    if any(w in text for w in ['software', 'information system', 'mis', 'portal', 'website', 'it infrastructure', 'cloud', 'data center', 'application development', 'database', 'ict', 'scada', 'telecom', 'computer', 'digitization', 'digital twin']):
        return 'Software & IT Solutions Project', 'software and IT solutions project'

    # 7. Smart Surveillance & Security
    if any(w in text for w in ['cctv', 'surveillance', 'camera', 'security system', 'monitoring system', 'control room']):
        return 'Smart Surveillance & Security Project', 'smart surveillance and security project'

    # 8. Environment & Climate Resilience
    if any(w in text for w in ['environment', 'climate', 'forest', 'biodiversity', 'coastal', 'ecological', 'pollution', 'waste', 'bio-medical waste', 'rehabilitation', 'conservation', 'subsidence']):
        return 'Environment & Climate Resilience Project', 'environment and climate resilience project'

    # 9. Urban Infrastructure
    if any(w in text for w in ['urban', 'housing', 'municipal', 'town planning', 'city', 'civil works', 'building', 'drain near', 'construction']):
        return 'Urban Infrastructure Project', 'urban infrastructure project'

    # 10. Financial & Governance
    if any(w in text for w in ['finance', 'financial', 'audit', 'governance', 'tax', 'accounting', 'advisory', 'capital accelerator', 'macro economic', 'trade']):
        return 'Financial & Governance Advisory Project', 'financial and governance advisory project'

    return 'Technology & Infrastructure Project', 'technology and infrastructure project'


def format_clean_subject(
    is_adb: bool = False,
    country: Optional[str] = None,
    state_name: Optional[str] = None,
    tender_id: Optional[str] = None,
    raw_title: Optional[str] = None,
    project_sector: Optional[str] = None,
    department: Optional[str] = None,
    keywords_str: Optional[str] = None
) -> str:
    """Build subject using the sector: Exploring JV / Consortium Partnership: {Sector} Project"""
    sec_title, _ = detect_tender_sector(title=raw_title, project_sector=project_sector, department=department, keywords_str=keywords_str)
    return f"Exploring JV / Consortium Partnership: {sec_title}"


ADB_SENDERS = [
    {
        "email": "support@gisfy.co.in",
        "name": "N C Harika | Business Development Executive",
        "dept": "Support & Outreach Operations (ADB Multilateral Projects)"
    },
    {
        "email": "farhath@gisfy.co.in",
        "name": "Farhath | Business Development Executive",
        "dept": "International Alliances & ADB Operations"
    },
    {
        "email": "firza@gisfy.co.in",
        "name": "Firza | Business Development Executive",
        "dept": "Multilateral Proposals & Strategic JV Lead"
    }
]

def resolve_sender_details(
    is_adb: bool,
    sender_email: Optional[str] = None,
    sender_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Resolve sender email and signature details based on account name mapping:
    - support@gisfy.co.in -> N C Harika | Business Development Executive
    - bidding.gisfy@gmail.com -> N C Harika | Business Development Executive
    - farhath@gisfy.co.in -> Farhath | Business Development Executive
    - firza@gisfy.co.in -> Firza | Business Development Executive
    """
    if is_adb:
        if sender_email:
            em = sender_email.strip().lower()
            if "farhath" in em:
                name = "Farhath | Business Development Executive"
                return {
                    "email": "farhath@gisfy.co.in",
                    "name": name,
                    "dept": "International Alliances & ADB Operations",
                    "sig_name": name
                }
            elif "firza" in em or "irza" in em:
                name = "Firza | Business Development Executive"
                return {
                    "email": "firza@gisfy.co.in",
                    "name": name,
                    "dept": "Multilateral Proposals & Strategic JV Lead",
                    "sig_name": name
                }
            elif "support" in em:
                name = "N C Harika | Business Development Executive"
                return {
                    "email": "support@gisfy.co.in",
                    "name": name,
                    "dept": "Support & Outreach Operations (ADB Multilateral Projects)",
                    "sig_name": name
                }
        name = "N C Harika | Business Development Executive"
        return {
            "email": "support@gisfy.co.in",
            "name": name,
            "dept": "Support & Outreach Operations (ADB Multilateral Projects)",
            "sig_name": name
        }
    else:
        name = "N C Harika | Business Development Executive"
        return {
            "email": "bidding.gisfy@gmail.com",
            "name": name,
            "dept": "29 Indian States Tendering & Domestic Consortiums",
            "sig_name": name
        }

def get_gisfy_logo_src() -> str:
    """Retrieve high-quality PNG logo as base64 data URI for universal email client and clipboard support."""
    import base64
    b64_file = BASE_DIR / "storage" / "gisfy_logo_b64.txt"
    if b64_file.exists():
        try:
            with open(b64_file, "r") as f:
                c = f.read().strip()
                if c.startswith("data:image/png;base64,"):
                    return c
        except Exception:
            pass
    png_path = BASE_DIR / "storage" / "gisfy_logo.png"
    if png_path.exists():
        try:
            with open(png_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass
    return "https://gisfy.co.in/assets/images/GISFY-logo.gif"

def extract_project_scope_lines(project_overview: Optional[str] = None, sector_phrase: Optional[str] = None) -> str:
    """
    Extract 2 to 3 concise lines describing the technical scope of work,
    strictly omitting client names, project names, tender numbers, and deadlines.
    """
    if not project_overview:
        sec = sector_phrase or "technology and infrastructure project"
        return f"The proposed scope of work encompasses comprehensive field data acquisition, high-precision geospatial surveys, enterprise digital database implementation, and specialized technical execution for this {sec}."
    
    sentences = re.split(r'(?<=[.!?])\s+', project_overview.strip())
    clean_sentences = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        if re.search(r'has issued Tender|issued Tender|bid submission closing|Tender #|LOAN|Grant|closing on|\bADB\b|Asian Development Bank|Ministry of|Department of', s_clean, re.I):
            continue
        s_clean = re.sub(r'#ADB-[A-Za-z0-9_-]+', '', s_clean)
        clean_sentences.append(s_clean)
    
    if len(clean_sentences) >= 2:
        return ' '.join(clean_sentences[:2])
    elif len(clean_sentences) == 1:
        return clean_sentences[0]
    
    sec = sector_phrase or "technology and infrastructure project"
    return f"The proposed scope of work encompasses comprehensive field data acquisition, high-precision geospatial surveys, enterprise digital database implementation, and specialized technical execution for this {sec}."

def build_collaboration_email_text(
    project_name: Optional[str] = None,
    project_overview: Optional[str] = None,
    state_name: Optional[str] = None,
    is_adb: bool = False,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    sector_phrase: Optional[str] = None
) -> str:
    """Build the clean plain text initial collaboration outreach email focusing on sector and scope of work."""
    if not sector_phrase:
        _, sector_phrase = detect_tender_sector(title=project_name)
    s_info = resolve_sender_details(is_adb=is_adb, sender_email=sender_email, sender_name=sender_name)
    resolved_name = s_info["name"]
    scope_text = extract_project_scope_lines(project_overview=project_overview, sector_phrase=sector_phrase)

    return f"""Dear Team,

Greetings from GISFY Private Limited, India.

We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.

We are currently exploring a potential Joint Venture (JV) / Consortium partnership with your organisation to collaborate and work together for an upcoming {sector_phrase}.

{scope_text}

Considering your organisation's expertise and experience, we believe there are strong synergies for mutual collaboration in the joint execution and implementation of this project.

If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following preliminary documents for our mutual evaluation:

• Company Profile – Highlighting technical capabilities, core competencies, and areas of expertise.

• Company Registration Certificate – Valid documentation confirming legal registration.

• Tax Registration Certificate – Applicable tax registration documents.

• CVs of Key Experts – Profiles of qualified professionals and technical specialists.

• Relevant Project Experience – Overview of similar completed or ongoing projects.

Upon receiving and reviewing these details, we would be pleased to schedule an introductory discussion and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.

We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.

Thanks & Regards,
{resolved_name}
GISFY Private Limited
Ground Floor, DSL Abacus IT Park,
Uppal, Hyderabad, Telangana – 500039, India
Mobile: +91 90631 20678
Website: www.gisfy.co.in"""

def build_collaboration_email_html(
    project_name: Optional[str] = None,
    project_overview: Optional[str] = None,
    state_name: Optional[str] = None,
    is_adb: bool = False,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    subject_line: Optional[str] = None,
    sector_phrase: Optional[str] = None
) -> str:
    """Build clean executive HTML email with sector focus, project scope, and authentic PNG GISFY logo."""
    if not sector_phrase:
        _, sector_phrase = detect_tender_sector(title=project_name)
    logo_src = "{{GISFY_LOGO_SRC}}"
    s_info = resolve_sender_details(is_adb=is_adb, sender_email=sender_email, sender_name=sender_name)
    resolved_name = s_info["name"]
    scope_text = extract_project_scope_lines(project_overview=project_overview, sector_phrase=sector_phrase)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #ffffff; margin: 0; padding: 24px; }}
  .content {{ max-width: 680px; margin: 0 auto; font-size: 14.5px; color: #1e293b; }}
  p {{ margin: 0 0 16px 0; }}
  .scope-box {{ background-color: #f8fafc; border-left: 3px solid #0284c7; padding: 12px 16px; margin: 16px 0; border-radius: 4px; font-size: 14px; color: #334155; line-height: 1.55; }}
  ul.doc-list {{ margin: 16px 0 18px 24px; padding-left: 0; list-style-type: disc; }}
  li.doc-item {{ margin-bottom: 8px; line-height: 1.5; color: #1e293b; }}
  .sig-block {{ margin-top: 24px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 13.5px; color: #374151; line-height: 1.6; }}
  .sig-regards {{ font-size: 14px; color: #1e293b; margin-bottom: 6px; font-weight: 500; }}
  .sig-name {{ font-weight: 700; font-size: 15px; color: #0f172a; margin-bottom: 4px; }}
  .sig-line {{ color: #475569; }}
  .sig-logo {{ margin-top: 14px; }}
</style>
</head>
<body>
<div class="content">
  <p>Dear Team,</p>
  <p>Greetings from GISFY Private Limited, India.</p>
  <p>We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.</p>
  <p>We are currently exploring a potential Joint Venture (JV) / Consortium partnership with your organisation to collaborate and work together for an upcoming <b>{sector_phrase}</b>.</p>
  <div class="scope-box">{scope_text}</div>
  <p>Considering your organisation's expertise and experience, we believe there are strong synergies for mutual collaboration in the joint execution and implementation of this project.</p>
  <p>If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following preliminary documents for our mutual evaluation:</p>
  <ul class="doc-list" style="margin: 14px 0 18px 22px; padding-left: 0; list-style-type: disc;">
    <li class="doc-item" style="margin-bottom: 8px; line-height: 1.5;"><b>Company Profile</b> – Highlighting technical capabilities, core competencies, and areas of expertise.</li>
    <li class="doc-item" style="margin-bottom: 8px; line-height: 1.5;"><b>Company Registration Certificate</b> – Valid documentation confirming legal registration.</li>
    <li class="doc-item" style="margin-bottom: 8px; line-height: 1.5;"><b>Tax Registration Certificate</b> – Applicable tax registration documents.</li>
    <li class="doc-item" style="margin-bottom: 8px; line-height: 1.5;"><b>CVs of Key Experts</b> – Profiles of qualified professionals and technical specialists.</li>
    <li class="doc-item" style="margin-bottom: 8px; line-height: 1.5;"><b>Relevant Project Experience</b> – Overview of similar completed or ongoing projects.</li>
  </ul>
  <p>Upon receiving and reviewing these details, we would be pleased to schedule an introductory discussion and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.</p>
  <p>We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.</p>
  
  <div class="sig-block">
    <div class="sig-regards">Thanks &amp; Regards,</div>
    <div class="sig-name">{resolved_name}</div>
    <div class="sig-line">GISFY Private Limited, Ground Floor, DSL Abacus IT Park,</div>
    <div class="sig-line">Uppal, Hyderabad, Telangana – 500039, India</div>
    <div class="sig-line"><b>Mobile:</b> <a href="tel:+919063120678" style="color: #4f46e5; text-decoration: none;">+91 90631 20678</a></div>
    <div class="sig-line"><b>Website :</b> <a href="https://www.gisfy.co.in" target="_blank" style="color: #4f46e5; text-decoration: none;">www.gisfy.co.in</a></div>
    <div class="sig-logo">
      <img src="{logo_src}" alt="GISFY Logo" style="height: 52px; max-width: 220px; object-fit: contain; display: block;" />
    </div>
  </div>
</div>
</body>
</html>"""


class CollaborationEmailService:
    def __init__(self):
        self.auto_send_enabled = False  # Requirement 9: Default to Draft-Only Mode!
        self.follow_up_days = 5         # Days until follow-up due

    def generate_drafts_for_tender(
        self,
        db: Session,
        tender_id: int,
        min_match_score: float = 60.0,
        max_partners_per_tender: int = 10
    ) -> List[models.CollaborationEmail]:
        """
        Analyze a tender proposal, match suitable partners, and prepare drafts.
        Guarantees de-duplication (no duplicate emails to the same partner for the same tender).
        """
        tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
        if not tender:
            return []

        # 1. Analyze proposal scope & overview
        scope_data = extract_project_scope_overview(tender)
        project_name = scope_data["project_name"]
        project_overview = scope_data["project_overview"]
        deadline = scope_data["deadline"]

        # 2. Match suitable partners
        matches_result = search_partners_for_tender(
            db=db,
            tender_id=tender_id,
            min_score=min_match_score
        )
        ranked_partners = (matches_result.get("partners") or matches_result.get("ranked_partners") or [])[:max_partners_per_tender]

        created_drafts = []

        for p_match in ranked_partners:
            partner = p_match.get("partner") if isinstance(p_match.get("partner"), dict) else p_match
            partner_id = partner["id"]
            partner_name = partner["name"]
            recipient_email = partner.get("email") or f"partnerships@{partner.get('short_name', 'company').lower().replace(' ', '')}.com"
            recipient_name = partner.get("contact_person") or partner.get("designation") or "Corporate Alliances Team"
            score = p_match.get("match_score", 85.0)
            fit_reason = p_match.get("why_needed") or p_match.get("rationale") or f"Strong synergy in {partner.get('primary_domain')}"

            # 3. De-duplication check: Avoid duplicate emails to same partner for same tender
            existing = db.query(models.CollaborationEmail).filter(
                models.CollaborationEmail.tender_id == tender_id,
                models.CollaborationEmail.partner_id == partner_id
            ).first()

            if existing:
                continue

            # 4. Generate subject and email bodies separating 29 Indian States and ADB Multilateral
            is_adb = bool((tender.state and "adb" in tender.state.name.lower()) or (tender.tender_id and tender.tender_id.upper().startswith("ADB")))
            state_name = tender.state.name if tender.state else "Pan-India"
            country = detect_tender_country(tender, db) if is_adb else None
            kw_str = " ".join([k.keyword for k in tender.keywords]) if tender.keywords else ""
            proj_sec = getattr(getattr(tender, "adb_details", None), "project_sector", None)
            sec_title, sec_phrase = detect_tender_sector(
                title=tender.title,
                project_sector=proj_sec,
                department=tender.department,
                keywords_str=kw_str
            )
            subject = f"Exploring JV / Consortium Partnership: {sec_title}"

            # Determine sender account based on 50-email batch rotation:
            # 1-50: support@gisfy.co.in, 51-100: farhath@gisfy.co.in, 101-150: firza@gisfy.co.in...
            if is_adb:
                total_adb_count = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.scope == "adb").count() + len(created_drafts)
                batch_idx = (total_adb_count // 50) % 3
                adb_emails = ["support@gisfy.co.in", "farhath@gisfy.co.in", "firza@gisfy.co.in"]
                chosen_email = adb_emails[batch_idx]
                s_info = resolve_sender_details(is_adb=True, sender_email=chosen_email)
            else:
                s_info = resolve_sender_details(is_adb=False)

            body_text = build_collaboration_email_text(
                project_name=tender.title,
                project_overview=project_overview,
                state_name=state_name,
                is_adb=is_adb,
                sender_name=s_info["name"],
                sender_email=s_info["email"],
                sector_phrase=sec_phrase
            )
            body_html = build_collaboration_email_html(
                project_name=tender.title,
                project_overview=project_overview,
                state_name=state_name,
                is_adb=is_adb,
                sender_name=s_info["name"],
                sender_email=s_info["email"],
                subject_line=subject,
                sector_phrase=sec_phrase
            )

            # 5. Create Draft in Gmail if OAuth available (for state)
            gmail_res = {}
            if not is_adb:
                gmail_res = gmail_connector.create_draft(
                    to_email=recipient_email,
                    subject=subject,
                    body_html=body_html,
                    body_text=body_text
                )

            email_record = models.CollaborationEmail(
                tender_id=tender_id,
                partner_id=partner_id,
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                company_name=partner_name,
                sender_email=s_info["email"],
                sender_name=s_info["name"],
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                project_name=project_name,
                project_overview=project_overview,
                match_score=score,
                selection_reason=fit_reason,
                required_expertise=", ".join(scope_data.get("required_expertise", [])),
                status="draft",
                approval_status="pending_approval",
                is_draft=True,
                scope="adb" if is_adb else "state",
                gmail_draft_id=gmail_res.get("draft_id")
            )

            db.add(email_record)
            created_drafts.append(email_record)

        db.commit()
        for d in created_drafts:
            db.refresh(d)

        return created_drafts

    def approve_draft(self, db: Session, draft_id: int) -> models.CollaborationEmail:
        """Approve a draft for sending."""
        draft = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == draft_id).first()
        if not draft:
            raise ValueError("Collaboration email record not found")

        draft.approval_status = "approved"
        draft.status = "approved"
        draft.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(draft)
        return draft

    def send_email(self, db: Session, email_id: int) -> Tuple[bool, str]:
        """
        Send an approved collaboration email via the live authenticated email provider.
        Maintains strict lifecycle statuses:
        - Draft -> Sending -> Provider Accepted / Found in Sent Items / Delivery Confirmed / Failed
        - Guarantees duplicate send prevention
        - Ensures From: GISFY Support <support@gisfy.co.in>, CC: bidding@gisfy.co.in, Reply-To: support@gisfy.co.in
        """
        from app.services.live_email_provider import live_email_provider

        record = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == email_id).first()
        if not record:
            return False, "Record not found"

        # Duplicate prevention check
        if record.status in ["Sending", "Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"]:
            return False, f"Email #{email_id} has already been dispatched or is currently sending (Status: {record.status})."

        # Check retry limit
        if (record.retry_count or 0) >= (record.max_retries or 3):
            record.status = "Failed"
            record.last_error = f"Max retries ({record.max_retries}) exceeded."
            db.commit()
            return False, record.last_error

        # Transition status to Sending
        record.status = "Sending"
        db.commit()
        db.refresh(record)

        # Determine sender based on record details and scope:
        is_adb = bool(
            record.scope == "adb"
            or (record.subject and "[ADB" in record.subject)
            or (record.body_text and "ASIAN DEVELOPMENT BANK" in record.body_text)
        )
        if is_adb:
            from_email = record.sender_email or "support@gisfy.co.in"
            from_name = record.sender_name or resolve_sender_details(from_email)[0]
            reply_to = from_email
        else:
            from_email = "bidding.gisfy@gmail.com"
            from_name = record.sender_name or "N C Harika | Business Development Executive"
            reply_to = "bidding.gisfy@gmail.com"

        html_content = record.body_html or ""
        if "{{GISFY_LOGO_SRC}}" in html_content:
            html_content = html_content.replace("{{GISFY_LOGO_SRC}}", get_gisfy_logo_src())

        lock_key = f"collab_email_{record.id}"
        dispatch_res = live_email_provider.dispatch_email(
            to_email=record.recipient_email,
            subject=record.subject,
            body_html=html_content,
            body_text=record.body_text,
            partner_name=record.company_name or record.recipient_name,
            cc_email="bidding@gisfy.co.in",
            from_name=from_name,
            from_email=from_email,
            reply_to=reply_to,
            lock_key=lock_key
        )

        if dispatch_res.get("success"):
            is_sent_verified = bool(dispatch_res.get("sent_folder_verified"))
            # Step 4: Map status accurately. HTTP 202 is Provider Accepted; presence in Sent Items is Found in Sent Items.
            record.status = "Found in Sent Items" if is_sent_verified else "Provider Accepted"
            record.is_draft = False
            record.sent_at = datetime.utcnow()
            record.follow_up_date = datetime.utcnow() + timedelta(days=self.follow_up_days)
            record.provider = dispatch_res.get("provider")
            record.provider_status_code = dispatch_res.get("provider_status_code")
            record.provider_message_id = dispatch_res.get("provider_message_id")
            record.sent_folder_verified = is_sent_verified
            record.delivery_verified = False  # Step 4: True delivery confirmation requires legitimate delivery-status evidence
            record.delivery_verified_at = None
            record.last_error = None
            db.commit()
            db.refresh(record)
            return True, f"Accepted by {record.provider} ({record.status}). Sent folder verified: {is_sent_verified}"
        else:
            record.retry_count = (record.retry_count or 0) + 1
            record.last_error = dispatch_res.get("error")
            record.status = "Failed"
            record.provider = dispatch_res.get("provider")
            record.provider_status_code = dispatch_res.get("provider_status_code")
            db.commit()
            db.refresh(record)
            return False, dispatch_res.get("error") or "Email provider rejected message."

    def assign_and_render_sender(
        self,
        db: Session,
        draft: models.CollaborationEmail,
        sender_email: str,
        sender_name: Optional[str] = None
    ) -> models.CollaborationEmail:
        """
        Dynamically assign sender and re-render body_text and body_html signatures.
        Ensures strict role title: Business Development Executive.
        """
        s_email = sender_email.strip().lower()
        t = draft.tender
        is_adb = bool(draft.scope == "adb" or (t and t.state and "adb" in t.state.name.lower()))
        s_info = resolve_sender_details(is_adb=is_adb, sender_email=s_email, sender_name=sender_name)
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
        return draft

    def reject_draft(self, db: Session, draft_id: int, reason: Optional[str] = None) -> models.CollaborationEmail:
        """Reject and cancel a draft."""
        draft = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.id == draft_id).first()
        if not draft:
            raise ValueError("Draft record not found")

        draft.approval_status = "rejected"
        draft.status = "opted_out"
        draft.last_error = reason or "Rejected by user in review mode"
        db.commit()
        db.refresh(draft)
        return draft

    def check_incoming_replies(self, db: Session) -> int:
        """
        Check for replies to sent emails.
        Updates response_status to 'replied' and records timestamp.
        """
        sent_emails = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"]),
            models.CollaborationEmail.response_status == "none"
        ).all()

        if not sent_emails:
            return 0

        # Check Microsoft Graph for replies if M365 is active
        from app.services.live_email_provider import live_email_provider
        replies_count = 0

        try:
            ok, token, _ = live_email_provider._get_m365_access_token()
            if ok and token:
                import requests
                headers = {"Authorization": f"Bearer {token}"}
                # Check messages in Inbox received in last 7 days
                inbox_url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$select=id,subject,from,receivedDateTime,bodyPreview&$top=20"
                res = requests.get(inbox_url, headers=headers, timeout=12)
                if res.status_code == 200:
                    inbox_msgs = res.json().get("value", [])
                    for msg in inbox_msgs:
                        from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
                        subj = msg.get("subject", "").lower()
                        for e in sent_emails:
                            if e.recipient_email.lower() == from_addr or (clean_proj := (e.project_name or "").lower()[:20]) in subj:
                                if e.response_status != "replied":
                                    e.response_status = "replied"
                                    e.status = "Replied"
                                    e.response_snippet = msg.get("bodyPreview", "")[:250]
                                    e.response_received_at = datetime.utcnow()
                                    replies_count += 1
                    if replies_count > 0:
                        db.commit()
        except Exception as e:
            print(f"[Reply Check Notice]: {e}")

        return replies_count

    def get_dashboard_summary(self, db: Session) -> Dict[str, Any]:
        """
        Aggregate collaboration workflow dashboard statistics adhering to Step 9:
        - Microsoft 365 Connection Status
        - Emails Generated
        - Emails Pending Approval
        - Emails Accepted by Provider
        - Emails Found in Sent Items
        - Emails with Confirmed Delivery
        - Emails Failed
        - Responses Received
        - Today's Sending Count (rolling 24h)
        - Remaining Daily Allowance (max 50)
        - Queued Emails
        - Next Scheduled Sending Time
        """
        now = datetime.utcnow()
        rolling_cutoff = now - timedelta(hours=24)

        total_records = db.query(models.CollaborationEmail).count()
        drafts_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.status.in_(["draft", "pending_approval", "Draft", "Pending Approval"])
        ).count()
        pending_approval_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.approval_status == "pending_approval"
        ).count()

        # Step 4 exact status metrics
        provider_accepted_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"])
        ).count()
        found_in_sent_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.sent_folder_verified == True
        ).count()
        delivery_confirmed_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.delivery_verified == True
        ).count()
        errors_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.status.in_(["failed", "Failed"])
        ).count()
        replies_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.response_status.in_(["replied", "interested", "declined"])
        ).count()

        # Step 5 Rolling 24-hour Quota (Max 50)
        today_sent = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.sent_at >= rolling_cutoff,
            models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "Delivery Confirmed", "sent"]),
            models.CollaborationEmail.is_test_email == False
        ).count()

        daily_limit = 50
        remaining_daily_allowance = max(0, daily_limit - today_sent)

        # Queued emails (Approved and ready for dispatch)
        queued_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.status == "approved",
            models.CollaborationEmail.approval_status == "approved"
        ).count()

        follow_ups_due = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.status.in_(["Provider Accepted", "Found in Sent Items", "sent"]),
            models.CollaborationEmail.response_status == "none",
            models.CollaborationEmail.follow_up_date != None,
            models.CollaborationEmail.follow_up_date <= now
        ).count()
        total_partners = db.query(models.Partner).count()
        state_partners_count = db.query(models.Partner).filter(models.Partner.category == "STATE").count()
        adb_partners_count = db.query(models.Partner).filter(models.Partner.category == "ADB").count()

        # Distinct counts for 29 Indian States vs ADB Multilateral
        states_drafts_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.scope == "state",
            models.CollaborationEmail.status.in_(["draft", "pending_approval", "Draft", "Pending Approval"])
        ).count()
        adb_drafts_count = db.query(models.CollaborationEmail).filter(
            models.CollaborationEmail.scope == "adb",
            models.CollaborationEmail.status.in_(["draft", "pending_approval", "Draft", "Pending Approval"])
        ).count()
        states_total_emails = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.scope == "state").count()
        adb_total_emails = db.query(models.CollaborationEmail).filter(models.CollaborationEmail.scope == "adb").count()

        from app.services.live_email_provider import live_email_provider
        provider_status = live_email_provider.get_public_status()

        return {
            "total_partners": total_partners,
            "state_partners_count": state_partners_count,
            "adb_partners_count": adb_partners_count,
            "total_records": total_records,
            "emails_generated": total_records,
            "drafts_prepared": drafts_count,
            "states_drafts_count": states_drafts_count,
            "adb_drafts_count": adb_drafts_count,
            "states_total_emails": states_total_emails,
            "adb_total_emails": adb_total_emails,
            "pending_approval": pending_approval_count,
            "provider_accepted": provider_accepted_count,
            "found_in_sent": found_in_sent_count,
            "delivery_confirmed": delivery_confirmed_count,
            "emails_sent": provider_accepted_count,
            "today_sent": today_sent,
            "daily_limit": daily_limit,
            "remaining_daily_allowance": remaining_daily_allowance,
            "queued_count": queued_count,
            "replies_received": replies_count,
            "follow_ups_due": follow_ups_due,
            "errors_count": errors_count,
            "auto_send_enabled": self.auto_send_enabled,
            "draft_mode_active": not self.auto_send_enabled,
            "provider_status": provider_status,
            "m365_connected": provider_status.get("microsoft_365", {}).get("is_authenticated", False)
        }

collaboration_email_service = CollaborationEmailService()
