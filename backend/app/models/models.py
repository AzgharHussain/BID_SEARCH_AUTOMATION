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

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    tender_row_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String)
    source_url = Column(Text)
    local_path = Column(Text)
    verified = Column(Boolean, default=False)
    download_status = Column(String, default="pending") # pending / downloaded / skipped_captcha
    portal_size_kb = Column(Float, nullable=True)
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

