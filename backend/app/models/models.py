from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    portal_url = Column(String)
    platform_type = Column(String)
    needs_login = Column(Boolean, default=False)
    has_captcha = Column(Boolean, default=False)
    status = Column(String, default="active")
    scraper_status = Column(String, default="working") # working / needs login / needs custom code / blocked

    tenders = relationship("Tender", back_populates="state")
    scrape_runs = relationship("ScrapeRun", back_populates="state")

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    source = Column(String, nullable=True)

class TenderKeyword(Base):
    __tablename__ = "tender_keywords"

    tender_row_id = Column(Integer, ForeignKey("tenders.id"), primary_key=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), primary_key=True)

class Tender(Base):
    __tablename__ = "tenders"
    __table_args__ = (UniqueConstraint('state_id', 'tender_id', name='uq_state_tender'),)

    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    tender_id = Column(String, index=True, nullable=False) # portal's own ID
    title = Column(Text, nullable=False)
    department = Column(String)
    published_date = Column(DateTime)
    last_date = Column(DateTime)
    portal_tender_url = Column(Text)
    description = Column(Text)
    relevance_score = Column(Float)
    relevance_reason = Column(Text)
    status = Column(String, default="new") # new/reviewed/applied/ignored
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    state = relationship("State", back_populates="tenders")
    documents = relationship("Document", back_populates="tender")
    keywords = relationship("Keyword", secondary="tender_keywords")
    adb_detail = relationship("AdbOpportunityDetail", back_populates="tender", uselist=False, cascade="all, delete-orphan")
    adb_tracker = relationship("AdbProposalTrack", back_populates="tender", uselist=False, cascade="all, delete-orphan")
    devex_detail = relationship("DevexOpportunityDetail", back_populates="tender", uselist=False, cascade="all, delete-orphan")
    devex_tracker = relationship("DevexProposalTrack", back_populates="tender", uselist=False, cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tender_row_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String)
    source_url = Column(Text)
    local_path = Column(Text)
    verified = Column(Boolean, default=False)
    download_status = Column(String, default="pending") # pending / downloaded / skipped_captcha / failed
    portal_size_kb = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    sha256_hash = Column(String, nullable=True)
    doc_category = Column(String, default="ATTACHMENT") # TOR / RFP / CSRN_NOTICE / EOI_FORM / ATTACHMENT / ADDENDUM
    doc_version = Column(String, default="1.0")
    access_status = Column(String, default="Verified") # Verified / Verification Pending / Missing / Restricted / Failed
    checksum_verified = Column(Boolean, default=False)
    retrieval_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", back_populates="documents")

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    status = Column(String) # running/success/failed
    tenders_found = Column(Integer, default=0)
    error_message = Column(Text)

    state = relationship("State", back_populates="scrape_runs")
    keyword = relationship("Keyword")

class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    short_name = Column(String, nullable=True)
    primary_domain = Column(String, index=True, nullable=False)
    secondary_domains = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    empanelment_status = Column(String, nullable=True)
    turnover = Column(String, nullable=True)
    employee_count = Column(String, nullable=True)
    country = Column(String, index=True, nullable=True)
    state = Column(String, index=True, nullable=True)
    city = Column(String, nullable=True)
    pan_india_presence = Column(Boolean, default=True)
    contact_person = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    past_projects = Column(Text, nullable=True)
    synergy_roles = Column(Text, nullable=True)
    rating = Column(Float, default=4.8)
    status = Column(String, default="Available")
    category = Column(String, default="STATE", index=True)  # 'STATE' (29 Indian States) | 'ADB' (Asian Development Bank & Multilateral)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TenderCollaboration(Base):
    __tablename__ = "tender_collaborations"
    __table_args__ = (UniqueConstraint('tender_id', 'partner_id', name='uq_tender_partner'),)

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)
    status = Column(String, default="Recommended")
    match_score = Column(Float, nullable=True)
    match_rationale = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender")
    partner = relationship("Partner")


class CollaborationEmail(Base):
    __tablename__ = "collaboration_emails"
    __table_args__ = (UniqueConstraint('tender_id', 'partner_id', name='uq_email_tender_partner'),)

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True, index=True)

    recipient_name = Column(String, nullable=True)
    recipient_email = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)

    subject = Column(String, nullable=False)
    body_text = Column(Text, nullable=False)
    body_html = Column(Text, nullable=False)

    project_name = Column(String, nullable=False)
    project_overview = Column(Text, nullable=False)
    match_score = Column(Float, default=85.0)
    selection_reason = Column(Text, nullable=True)
    required_expertise = Column(Text, nullable=True)

    # Status: 'Draft', 'Sending', 'Provider Accepted', 'Failed', 'Delivery Confirmed'
    status = Column(String, default="Draft", index=True)
    approval_status = Column(String, default="pending_approval", index=True)  # 'pending_approval', 'approved', 'rejected'
    is_draft = Column(Boolean, default=True)
    scope = Column(String, default="state", index=True)  # 'state' (29 Indian States) | 'adb' (Asian Development Bank)
    sender_email = Column(String, nullable=True, index=True)
    sender_name = Column(String, nullable=True)

    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True, index=True)
    follow_up_date = Column(DateTime, nullable=True, index=True)
    follow_up_count = Column(Integer, default=0)

    # Response tracking: 'none', 'replied', 'interested', 'declined', 'opted_out'
    response_status = Column(String, default="none", index=True)
    response_received_at = Column(DateTime, nullable=True)
    response_snippet = Column(Text, nullable=True)

    # Live Provider & Verification tracking (Microsoft Graph OAuth2, Google, SMTP)
    provider = Column(String, nullable=True)
    provider_status_code = Column(Integer, nullable=True)
    provider_message_id = Column(String, nullable=True)
    provider_response_raw = Column(Text, nullable=True)
    sent_folder_verified = Column(Boolean, default=False)
    delivery_verified = Column(Boolean, default=False)
    delivery_verified_at = Column(DateTime, nullable=True)
    is_test_email = Column(Boolean, default=False)

    gmail_message_id = Column(String, nullable=True)
    gmail_thread_id = Column(String, nullable=True)
    gmail_draft_id = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender")
    partner = relationship("Partner")


class CollaborationWorkflowLog(Base):
    __tablename__ = "collaboration_workflow_logs"

    id = Column(Integer, primary_key=True, index=True)
    cycle_type = Column(String, default="daily_scheduled")  # 'daily_scheduled', 'manual_trigger'
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    tenders_analyzed = Column(Integer, default=0)
    partners_matched = Column(Integer, default=0)
    drafts_created = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    replies_checked = Column(Integer, default=0)
    follow_ups_flagged = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    status = Column(String, default="running")  # 'running', 'success', 'completed_with_errors', 'failed'
    log_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdbOpportunityDetail(Base):
    __tablename__ = "adb_opportunity_details"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), unique=True, nullable=False, index=True)
    csrn_id = Column(String, index=True, nullable=False)
    selection_number = Column(String, index=True, nullable=True)
    package_number = Column(String, index=True, nullable=True)
    project_number = Column(String, index=True, nullable=True)
    country = Column(String, index=True, nullable=True)
    executing_agency = Column(Text, nullable=True)
    implementing_agency = Column(Text, nullable=True)
    project_sector = Column(String, index=True, nullable=True)
    consultant_type = Column(String, nullable=True)  # 'Firm' / 'Individual'
    consultant_source = Column(String, nullable=True)  # 'International' / 'National' / 'International/National'
    selection_method = Column(String, nullable=True)  # 'QCBS', 'FBS', 'QBS', 'CQS', 'ICS', etc.
    technical_proposal_type = Column(String, nullable=True)  # 'Full Technical Proposal (FTP)', 'STP', 'BTP'
    budget_amount = Column(Float, nullable=True)
    budget_currency = Column(String, default="USD")
    budget_type = Column(String, nullable=True)  # 'Estimated' / 'Maximum'
    engagement_period_months = Column(Float, nullable=True)
    advance_action = Column(Boolean, default=False)
    approval_number = Column(String, nullable=True)
    approval_date = Column(String, nullable=True)
    estimated_commencement_date = Column(String, nullable=True)
    open_to_non_member = Column(Boolean, default=False)
    publication_date_str = Column(String, nullable=True)
    eoi_deadline_str = Column(String, nullable=True)  # Manila local time as published
    eoi_deadline_ist = Column(DateTime, nullable=True)  # Exact IST calculated when timezone verified
    proposal_deadline = Column(DateTime, nullable=True)
    source_timezone = Column(String, default="Manila local time (UTC+8)")
    scope_of_work = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    qualification_requirements = Column(Text, nullable=True)
    jv_consortium_rules = Column(Text, nullable=True)
    contact_officer = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    official_source_url = Column(Text, nullable=True)
    raw_details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender", back_populates="adb_detail")


class AdbProposalTrack(Base):
    __tablename__ = "adb_proposal_tracks"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), unique=True, nullable=False, index=True)

    # Pipeline Stages:
    # 'Opportunity Identified', 'Under Review', 'EOI In Preparation', 'EOI Submitted',
    # 'Shortlisted', 'RFP Received', 'Technical Proposal', 'Financial Proposal',
    # 'Submitted', 'Evaluation', 'Awarded / Not Awarded'
    pipeline_stage = Column(String, default="Opportunity Identified", index=True)
    stage_status = Column(String, default="manual_entry")  # 'source_verified', 'manual_entry', 'unavailable'
    submission_reference = Column(String, nullable=True)
    cms_acknowledgement_id = Column(String, nullable=True)
    lead_partner_name = Column(String, nullable=True)
    internal_notes = Column(Text, nullable=True)
    target_submission_date = Column(DateTime, nullable=True)
    history_json = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", back_populates="adb_tracker")


class AdbSyncLog(Base):
    __tablename__ = "adb_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String, default="scheduled")  # 'scheduled', 'manual_now', 'retry_failed'
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    opportunities_found = Column(Integer, default=0)
    opportunities_added = Column(Integer, default=0)
    opportunities_updated = Column(Integer, default=0)
    documents_downloaded = Column(Integer, default=0)
    documents_missing = Column(Integer, default=0)
    documents_failed = Column(Integer, default=0)
    status = Column(String, default="running")  # 'running', 'success', 'completed_with_errors', 'failed'
    error_message = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)


class DevexOpportunityDetail(Base):
    """
    Devex International Procurement Opportunity Detail Model.
    Captures comprehensive, genuine procurement metadata across donors worldwide
    (World Bank, UN/UNDP, USAID, AfDB, IDB, Millennium Challenge Corp, etc.).
    Preserves authentic donor reference numbers, original timezones, and official links.
    """
    __tablename__ = "devex_opportunity_details"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), unique=True, nullable=False, index=True)
    
    # Identifiers & Sources
    devex_id = Column(String, index=True, nullable=True)  # Devex reference ID (e.g. DEVEX-OPP-104928)
    original_procurement_ref = Column(String, index=True, nullable=True)  # Official donor reference (e.g. WB-P173829-CS01)
    donor_agency = Column(String, index=True, nullable=False)  # World Bank, UNDP, USAID, AfDB, etc.
    executing_agency = Column(Text, nullable=True)
    implementing_agency = Column(Text, nullable=True)
    
    # Geography & Classification
    country = Column(String, index=True, nullable=True)
    region = Column(String, index=True, nullable=True)  # Sub-Saharan Africa, South Asia, etc.
    project_sector = Column(String, index=True, nullable=True)  # GIS, Water, Infrastructure, etc.
    procurement_category = Column(String, nullable=True)  # Consulting Services, Goods, Works
    opportunity_type = Column(String, default="Tenders and Open Opportunities", index=True)  # Open Tenders, Grants, Awards
    
    # Dates, Deadlines & Financials
    publication_date_str = Column(String, nullable=True)
    submission_deadline_str = Column(String, nullable=True)  # Original as published with timezone
    deadline_time = Column(String, nullable=True)
    deadline_timezone = Column(String, nullable=True)  # e.g. "EST (UTC-5)", "UTC", "CET"
    deadline_ist = Column(DateTime, nullable=True)  # Calculated IST equivalent when timezone verified
    estimated_value = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    project_duration = Column(String, nullable=True)  # e.g. "24 Months"
    
    # Technical & Scope Details
    objectives = Column(Text, nullable=True)
    scope_of_work = Column(Text, nullable=True)
    technical_requirements = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    qualification_requirements = Column(Text, nullable=True)
    jv_consortium_rules = Column(Text, nullable=True)
    required_experts = Column(Text, nullable=True)
    
    # Official Source Links & Documents
    official_donor_website = Column(Text, nullable=True)  # Donor's procurement website
    official_tender_url = Column(Text, nullable=True)  # Direct official tender link
    devex_url = Column(Text, nullable=True)  # Devex funding reference link
    document_availability = Column(String, default="Publicly Available from Donor")  # Public, Registered, Restricted
    
    # Integration & Verification Compliance
    integration_mode = Column(String, default="Option B: Business Alert Ingestion")  # Option A, B, C, D
    last_verified_at = Column(DateTime, default=datetime.utcnow)
    raw_details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender", back_populates="devex_detail")


class DevexProposalTrack(Base):
    """
    Tracks GISFY's proposal progression for Devex international opportunities.
    Workflow stages:
    Opportunity Identified -> Under Evaluation -> Eligible -> EOI Preparation ->
    EOI Submitted -> Shortlisted -> RFP Received -> Technical Proposal Preparation ->
    Financial Proposal Preparation -> Proposal Submitted -> Under Evaluation by Client ->
    Awarded / Not Awarded / Closed
    """
    __tablename__ = "devex_proposal_tracks"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), unique=True, nullable=False, index=True)

    pipeline_stage = Column(String, default="Opportunity Identified", index=True)
    stage_status = Column(String, default="manual_entry")  # 'source_verified', 'manual_entry'
    submission_portal = Column(String, nullable=True)  # Official portal name (NOT Devex)
    submission_reference = Column(String, nullable=True)
    lead_partner_name = Column(String, nullable=True)
    consortium_partners_json = Column(Text, nullable=True)
    target_submission_date = Column(DateTime, nullable=True)
    internal_notes = Column(Text, nullable=True)
    readiness_score = Column(Float, nullable=True)
    winnability_summary = Column(Text, nullable=True)
    history_json = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", back_populates="devex_tracker")


class DevexSyncLog(Base):
    """Tracks synchronization runs for Devex opportunity ingestion."""
    __tablename__ = "devex_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String, default="alert_ingestion")  # alert_ingestion, donor_enrichment, manual_import, api_feed
    integration_mode = Column(String, default="Option B: Business Alert Ingestion")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    opportunities_found = Column(Integer, default=0)
    opportunities_added = Column(Integer, default=0)
    opportunities_updated = Column(Integer, default=0)
    documents_downloaded = Column(Integer, default=0)
    documents_missing = Column(Integer, default=0)
    documents_failed = Column(Integer, default=0)
    status = Column(String, default="running")  # running, success, completed_with_errors, failed
    error_message = Column(Text, nullable=True)
    summary_json = Column(Text, nullable=True)


class MasterOpportunityLink(Base):
    """
    Module 8: Cross-Source Deduplication & Unified Master Linkage.
    Links the same procurement opportunity appearing across different sources
    (e.g. Devex, ADB CMS, World Bank, UNGM) under one unified Master Opportunity record
    while preserving all individual source references and links.
    """
    __tablename__ = "master_opportunity_links"

    id = Column(Integer, primary_key=True, index=True)
    master_ref = Column(String, index=True, nullable=False)  # Normalized cross-source key
    primary_tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    source_system = Column(String, index=True, nullable=False)  # 'devex', 'adb_cms', 'state_tender', etc.
    source_tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    match_confidence = Column(Float, default=1.0)
    match_criteria = Column(Text, nullable=True)  # JSON explaining why matched (ref_number, title_similarity, url)
    is_master = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


