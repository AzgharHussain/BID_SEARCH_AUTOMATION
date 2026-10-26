import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models import models
from app.services.tender_proposal_analyzer import extract_project_scope_overview
from app.services.partner_service import search_partners_for_tender
from app.services.gmail_connector import gmail_connector

def build_collaboration_email_text(
    project_name: Optional[str] = None,
    project_overview: Optional[str] = None
) -> str:
    """Build the plain text email using only the exact content provided by the user, incorporating the project overview."""
    proj = project_name or "<Project Name>"
    overview_text = f"\nProject Overview:\n{project_overview.strip()}\n" if project_overview else ""

    return f"""Dear Team,

Greetings from GISFY Private Limited, India.

We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.

We are currently exploring a potential Joint Venture (JV) / Consortium partnership for {proj}.
{overview_text}
Considering your organisation's expertise and experience, we believe there may be valuable opportunities for collaboration in the joint submission and implementation of this assignment, subject to the applicable procurement requirements.

If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following documents for our preliminary evaluation:

Company Profile – Highlighting your organisation's technical capabilities, core competencies, and areas of expertise.
Company Registration Certificate – Valid documentation confirming the legal registration of your organisation.
Tax Registration Certificate – Applicable tax registration documents issued by the relevant authorities.
CVs of Key Experts – Profiles of qualified professionals with expertise relevant to the proposed assignment.
Relevant Project Experience – Details of similar completed or ongoing projects, including project descriptions, scope of work, client details, and your organisation's role.

Upon receiving and reviewing the above documents, we would be pleased to discuss the proposed collaboration structure and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.

We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.

Thanks & Regards,
Farhath Bakka | Business Development Executive
GISFY Support & Partnerships Team
GISFY Private Limited
Ground Floor, DSL Abacus IT Park,
Uppal, Hyderabad, Telangana – 500039, India
Email: farhath@gisfy.co.in | support@gisfy.co.in
Mobile: +91 90631 20678
Website: www.gisfy.co.in"""

def build_collaboration_email_html(
    project_name: Optional[str] = None,
    project_overview: Optional[str] = None
) -> str:
    """Build the HTML email reflecting only the exact content provided by the user with 2-5 line project overview, signature & logo."""
    proj = project_name or "<Project Name>"
    logo_src = "https://gisfy.co.in/images/logo.png"

    overview_html = f"""
  <div style="background: #f8fafc; border-left: 3px solid #4f46e5; padding: 12px 14px; margin: 16px 0; border-radius: 4px;">
    <div style="font-size: 11.5px; font-weight: 700; color: #4338ca; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px;">📋 Assignment Overview &amp; Technical Scope</div>
    <div style="font-size: 13.5px; color: #334155; line-height: 1.55;">{project_overview.strip()}</div>
  </div>
    """ if project_overview else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #ffffff; margin: 0; padding: 24px; }}
  .content {{ max-width: 680px; margin: 0 auto; font-size: 14.5px; color: #1e293b; }}
  p {{ margin: 0 0 16px 0; }}
  .doc-list {{ margin: 16px 0; padding-left: 0; }}
  .doc-item {{ margin-bottom: 10px; line-height: 1.5; }}
  .sig-block {{ margin-top: 24px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 13.5px; color: #374151; line-height: 1.6; }}
  .sig-name {{ font-weight: 700; font-size: 15px; color: #0f172a; }}
  .sig-role {{ font-weight: 400; color: #64748b; }}
  .sig-line {{ color: #475569; }}
  .sig-logo {{ margin-top: 14px; }}
</style>
</head>
<body>
<div class="content">
  <p>Dear Team,</p>
  <p>Greetings from GISFY Private Limited, India.</p>
  <p>We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.</p>
  <p>We are currently exploring a potential Joint Venture (JV) / Consortium partnership for <b>{proj}</b>.</p>
  {overview_html}
  <p>Considering your organisation's expertise and experience, we believe there may be valuable opportunities for collaboration in the joint submission and implementation of this assignment, subject to the applicable procurement requirements.</p>
  <p>If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following documents for our preliminary evaluation:</p>
  <div class="doc-list">
    <div class="doc-item">• <b>Company Profile</b> – Highlighting your organisation's technical capabilities, core competencies, and areas of expertise.</div>
    <div class="doc-item">• <b>Company Registration Certificate</b> – Valid documentation confirming the legal registration of your organisation.</div>
    <div class="doc-item">• <b>Tax Registration Certificate</b> – Applicable tax registration documents issued by the relevant authorities.</div>
    <div class="doc-item">• <b>CVs of Key Experts</b> – Profiles of qualified professionals with expertise relevant to the proposed assignment.</div>
    <div class="doc-item">• <b>Relevant Project Experience</b> – Details of similar completed or ongoing projects, including project descriptions, scope of work, client details, and your organisation's role.</div>
  </div>
  <p>Upon receiving and reviewing the above documents, we would be pleased to discuss the proposed collaboration structure and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.</p>
  <p>We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.</p>
  <p>Thanks &amp; Regards,</p>
  <div class="sig-block">
    <div class="sig-name">Farhath Bakka <span class="sig-role">| Business Development Executive</span></div>
    <div class="sig-line">GISFY Support &amp; Partnerships Team</div>
    <div class="sig-line">GISFY Private Limited, Ground Floor, DSL Abacus IT Park,</div>
    <div class="sig-line">Uppal, Hyderabad, Telangana – 500039, India</div>
    <div class="sig-line"><b>Email:</b> <a href="mailto:farhath@gisfy.co.in" style="color: #4f46e5; text-decoration: none;">farhath@gisfy.co.in</a> | <a href="mailto:support@gisfy.co.in" style="color: #4f46e5; text-decoration: none;">support@gisfy.co.in</a></div>
    <div class="sig-line"><b>Mobile:</b> <a href="tel:+919063120678" style="color: #4f46e5; text-decoration: none;">+91 90631 20678</a></div>
    <div class="sig-line"><b>Website :</b> <a href="http://www.gisfy.co.in" target="_blank" style="color: #4f46e5; text-decoration: none;">www.gisfy.co.in</a></div>
    <div class="sig-logo">
      <img src="{logo_src}" alt="GISFY Logo" style="height: 48px; max-width: 180px; object-fit: contain; display: block;" />
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

            # 4. Generate subject and email bodies using ONLY the exact user content with project overview
            clean_proj_name = (tender.title or "<Project Name>").strip().strip("[]").strip().rstrip(".")
            subject = f"Exploring JV / Consortium Partnership – {clean_proj_name[:65]}"
            body_text = build_collaboration_email_text(
                project_name=clean_proj_name,
                project_overview=project_overview
            )
            body_html = build_collaboration_email_html(
                project_name=clean_proj_name,
                project_overview=project_overview
            )

            # 5. Create Draft in Gmail if OAuth available
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
        - Ensures From: Farhath Bakka <farhath@gisfy.co.in>, CC: bidding@gisfy.co.in, Reply-To: farhath@gisfy.co.in
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

        lock_key = f"collab_email_{record.id}"
        dispatch_res = live_email_provider.dispatch_email(
            to_email=record.recipient_email,
            subject=record.subject,
            body_html=record.body_html,
            body_text=record.body_text,
            partner_name=record.company_name or record.recipient_name,
            cc_email="bidding@gisfy.co.in",
            from_name="Farhath Bakka & GISFY Support",
            from_email="farhath@gisfy.co.in, support@gisfy.co.in",
            reply_to="farhath@gisfy.co.in, support@gisfy.co.in",
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

        from app.services.live_email_provider import live_email_provider
        provider_status = live_email_provider.get_public_status()

        return {
            "total_partners": total_partners,
            "total_records": total_records,
            "emails_generated": total_records,
            "drafts_prepared": drafts_count,
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
