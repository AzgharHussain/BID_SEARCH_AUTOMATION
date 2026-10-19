from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

class DocumentSchema(BaseModel):
    file_name: str
    file_type: Optional[str] = None
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    verified: bool = False
    download_status: str = "pending"
    portal_size_kb: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class TenderBase(BaseModel):
    tender_id: str
    title: str
    department: Optional[str] = None
    published_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    portal_tender_url: Optional[str] = None
    description: Optional[str] = None

class TenderCreate(TenderBase):
    pass

class TenderSchema(TenderBase):
    id: int
    state_id: int
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentSchema] = []

    model_config = ConfigDict(from_attributes=True)

# Payload from the scraper
class ScraperDocument(BaseModel):
    file_name: str
    file_type: Optional[str] = None
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    download_status: str = "pending"
    portal_size_kb: Optional[float] = None

class ScraperIngestPayload(BaseModel):
    state_name: str = Field(..., description="Name of the state, must match existing state record")
    keyword: str = Field(..., description="The keyword used during the scrape run")
    tender_id: str = Field(..., description="Portal's own ID for the tender")
    title: str
    department: Optional[str] = None
    published_date: Optional[datetime] = None
    last_date: Optional[datetime] = None
    portal_tender_url: Optional[str] = None
    description: Optional[str] = None
    documents: List[ScraperDocument] = []

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "state_name": "Maharashtra",
                    "keyword": "Solar",
                    "tender_id": "MH-2023-SOLAR-001",
                    "title": "Installation of Solar Panels in Government Schools",
                    "department": "Energy Department",
                    "published_date": "2023-10-01T10:00:00Z",
                    "last_date": "2023-10-30T17:00:00Z",
                    "portal_tender_url": "https://mahatenders.gov.in/tender/1",
                    "description": "Supply, installation and commissioning of 10KW solar plants in 50 schools.",
                    "documents": [
                        {
                            "file_name": "nit_document.pdf",
                            "file_type": "application/pdf",
                            "source_url": "https://mahatenders.gov.in/docs/nit_document.pdf",
                            "local_path": "/storage/Maharashtra/Solar/MH-2023-SOLAR-001/nit_document.pdf"
                        }
                    ]
                }
            ]
        }
    }

class ScrapeRunCreate(BaseModel):
    state_id: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    status: str
    tenders_found: int = 0
    error_message: Optional[str] = None

class ScrapeRunSchema(ScrapeRunCreate):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class StateSchema(BaseModel):
    id: int
    name: str
    portal_url: Optional[str]
    platform_type: Optional[str]
    needs_login: bool
    has_captcha: bool
    status: str
    scraper_status: str

    model_config = ConfigDict(from_attributes=True)

class StateCreate(BaseModel):
    name: str
    portal_url: Optional[str] = None
    platform_type: Optional[str] = None
    needs_login: bool = False
    has_captcha: bool = False
    status: str = "active"
    scraper_status: str = "working"

class KeywordSchema(BaseModel):
    id: int
    keyword: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class KeywordCreate(BaseModel):
    keyword: str
    is_active: bool = True

class PartnerBase(BaseModel):
    name: str
    short_name: Optional[str] = None
    primary_domain: str
    secondary_domains: Optional[str] = None
    description: Optional[str] = None
    certifications: Optional[str] = None
    empanelment_status: Optional[str] = None
    turnover: Optional[str] = None
    employee_count: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pan_india_presence: bool = True
    contact_person: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    past_projects: Optional[str] = None
    synergy_roles: Optional[str] = None
    rating: Optional[float] = 4.8
    status: Optional[str] = "Available"

class PartnerCreate(PartnerBase):
    pass

class PartnerUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    primary_domain: Optional[str] = None
    secondary_domains: Optional[str] = None
    description: Optional[str] = None
    certifications: Optional[str] = None
    empanelment_status: Optional[str] = None
    turnover: Optional[str] = None
    employee_count: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    pan_india_presence: Optional[bool] = None
    contact_person: Optional[str] = None
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    past_projects: Optional[str] = None
    synergy_roles: Optional[str] = None
    rating: Optional[float] = None
    status: Optional[str] = None

class PartnerSchema(PartnerBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class TenderMatchedPartnerSchema(PartnerSchema):
    match_score: float
    match_category: str
    why_needed: str
    synergy_scope: str
    collaboration_status: str
    collaboration_notes: Optional[str] = None

class TenderCollaborationStatusUpdate(BaseModel):
    tender_id: int
    partner_id: int
    status: str
    notes: Optional[str] = None

class OutreachProposalRequest(BaseModel):
    tender_id: int
    partner_id: int
    gisfy_contact_name: Optional[str] = "GISFY Proposals Directorate"
    gisfy_contact_email: Optional[str] = "tenders@gisfy.co.in"
    custom_message: Optional[str] = None
    proposed_jv_split: Optional[str] = "60% Lead Bidder (GISFY) : 40% Specialized Partner"

class OutreachProposalResponse(BaseModel):
    partner_id: int
    partner_name: str
    partner_email: Optional[str]
    tender_id: str
    tender_title: str
    state_name: str
    department: Optional[str]
    due_date: Optional[str]
    subject: str
    proposal_letter: str
    collaboration_status: str

