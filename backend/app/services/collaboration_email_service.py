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


# Comprehensive patterns for tailoring technical scope dynamically to projects/tenders
# Strict format:
# Sentence 1: The assignment encompasses {act1}, {act2}, and {act3}.
# Sentence 2: Key technical requirements involve {req1}, {req2}, quality assurance, and {req3}.
PROJECT_TECHNICAL_SCOPE_PATTERNS = [
    # 1. CCTV, Smart Surveillance & Security Control Rooms
    (
        'surveillance',
        re.compile(r'\b(cctv|surveillance|cameras?|security systems?|control rooms?|command cent(?:er|re)|vms|video management|access control)\b', re.I),
        (
            'The assignment encompasses comprehensive field deployment of high-definition CCTV surveillance infrastructure, network video recording integration with multi-point sensor arrays, and the operationalization of a centralized digital security control room.',
            'Key technical requirements involve High-Definition Video Surveillance Systems, Network Video Recording & allied IT Infrastructure, quality assurance, and integration with centralized real-time security monitoring systems.',
            'smart surveillance and security project',
            'Smart Surveillance & Security Project'
        )
    ),
    # 2. Roads, Highways, Corridors & Pavements
    (
        'transport',
        re.compile(r'\b(highways?|roads?|corridors?|pavements?|bridges?|flyovers?|expressways?|culverts?|carriageways?|traffic engineering|traffic management|toll plaza|ser-\d+)\b', re.I),
        (
            'The assignment encompasses comprehensive road asset inventory acquisition, high-precision corridor condition surveys, and the deployment of an enterprise digital transportation infrastructure database.',
            'Key technical requirements involve Road Asset Management Systems, Pavement Condition & Corridor Spatial Engineering, quality assurance, and integration with public transportation monitoring systems.',
            'transport and infrastructure project',
            'Transport & Infrastructure Project'
        )
    ),
    # 3. Railways & Mass Rapid Transit
    (
        'railway',
        re.compile(r'\b(railways?|rapid transit|metro rail|rail tracks?|rolling stocks?|freight corridor)\b', re.I),
        (
            'The assignment encompasses railway alignment data acquisition, high-precision permanent way and asset surveys, and the deployment of a centralized digital railway infrastructure database.',
            'Key technical requirements involve Transit Corridor Spatial Analytics, Railway Track & Asset Engineering, quality assurance, and integration with operational train monitoring systems.',
            'railway and mass transit project',
            'Railway & Mass Transit Project'
        )
    ),
    # 4. Drone, LiDAR, Cadastral & Core WebGIS
    (
        'geospatial',
        re.compile(r'\b(drones?|uavs?|lidar|dgps|cadastral|photogrammetry|gis mapping|geospatial|remote sensing|topographic surveys?|cartograph\w*|webgis)\b', re.I),
        (
            'The assignment encompasses comprehensive field data acquisition, high-precision geospatial surveys, and the deployment of an enterprise WebGIS digital database.',
            'Key technical requirements involve Enterprise GIS Solutions, Digital Surveying & Geodatabase Engineering, quality assurance, and integration with public infrastructure monitoring systems.',
            'geospatial and digital survey project',
            'Geospatial & Digital Survey Project'
        )
    ),
    # 5. Electro-Mechanical, Facility Maintenance & ARMO/RMO
    (
        'facility',
        re.compile(r'\b(armo|rmo|e\s*&\s*m|e and m|electro-mechanical|firefighting|cooling towers?|dg sets?|hvac|air conditioning|plumbing|sanitary works?|repair of existing|maintenance of existing)\b', re.I),
        (
            'The assignment encompasses electro-mechanical facility assessment, infrastructure asset inventorying, and the deployment of an enterprise facility operations digital database.',
            'Key technical requirements involve Electro-Mechanical Systems Engineering, Facility Maintenance & Asset Registry Management, quality assurance, and integration with facility operations monitoring systems.',
            'facility operations and infrastructure project',
            'Facility Operations & Infrastructure Project'
        )
    ),
    # 6. Water Resources, Irrigation, Dams & Hydrology
    (
        'water',
        re.compile(r'\b(water resources?|iwrm|irrigat\w*|hydrolog\w*|drainage|flood\w*|\bdams?\b|canals?|river basins?|water supply|watersheds?|aquifers?|reservoirs?|wastewater|sewerage|water balance|water security|hydrogeolog\w*)\b', re.I),
        (
            'The assignment encompasses comprehensive hydrological data acquisition, water distribution asset mapping and catchment surveys, and the deployment of an enterprise water resource management digital database.',
            'Key technical requirements involve Hydrological Modeling & Water Network Engineering, Spatial Asset Inventory & Geodatabase Solutions, quality assurance, and integration with public water infrastructure monitoring systems.',
            'water resources project',
            'Water Resources Project'
        )
    ),
    # 7. Energy, Power, Solar & SCADA
    (
        'energy',
        re.compile(r'\b(solar|power sector|power grid|power plant|photovoltaic|substations?|\bgrids?\b|electricity|decarbonization|transmissions?|scada|transformers?|electrical works?|electrification)\b', re.I),
        (
            'The assignment encompasses power network asset characterization, renewable energy site mapping and electrical equipment evaluation, and the deployment of an enterprise digital power distribution database.',
            'Key technical requirements involve Power Transmission & Distribution Asset Engineering, Solar PV & SCADA System Integration, quality assurance, and integration with public utility monitoring systems.',
            'energy and power sector project',
            'Energy & Power Sector Project'
        )
    ),
    # 8. Environment, Climate Resilience & Bio-Medical Waste
    (
        'environment',
        re.compile(r'\b(environments?|forest\w*|climates?|waste management|bio-medical|pollution|ecolog\w*|biodiversity|rehabilitation|conservation|subsidence|effluents?|sanitation|garbage)\b', re.I),
        (
            'The assignment encompasses comprehensive baseline environmental data collection, ecological habitat and emissions mapping, and the deployment of an enterprise digital environmental database.',
            'Key technical requirements involve Environmental Impact Assessment Solutions, Ecological Monitoring & Geodatabase Engineering, quality assurance, and integration with statutory environmental compliance systems.',
            'environment and climate resilience project',
            'Environment & Climate Resilience Project'
        )
    ),
    # 9. Agriculture & Rural Development
    (
        'agriculture',
        re.compile(r'\b(agricultur\w*|farmlands?|\bcrops?\b|agroforestry|rural livelihoods?|smallholders?|farming|horticultur\w*|livestock|veterinary|\bsoils?\b)\b', re.I),
        (
            'The assignment encompasses agricultural land parcel data acquisition, high-resolution crop health and vegetation surveys, and the deployment of an enterprise digital agricultural database.',
            'Key technical requirements involve Agri-Spatial Analytics & Remote Sensing, Land Capability & Crop Health Assessment, quality assurance, and integration with agricultural decision support systems.',
            'agriculture and rural development project',
            'Agriculture & Rural Development Project'
        )
    ),
    # 10. Healthcare & Biomedical Systems
    (
        'healthcare',
        re.compile(r'\b(healthcare|hospitals?|medical|clinical|epidemiolog\w*|patients?|telemedicine|dispensar\w*)\b', re.I),
        (
            'The assignment encompasses comprehensive healthcare facility inventorying, spatial health infrastructure assessments, and the deployment of a centralized healthcare digital database.',
            'Key technical requirements involve Public Health Analytics Solutions, Clinical Asset & Health Informatics Engineering, quality assurance, and integration with public healthcare monitoring systems.',
            'healthcare systems project',
            'Healthcare Systems Project'
        )
    ),
    # 11. Software, IT Solutions, Cloud & MIS
    (
        'software',
        re.compile(r'\b(softwares?|information systems?|\bmis\b|web portals?|web applications?|cloud computing|data cent(?:er|re)|application development|databases?|\bict\b|digitization|digital twins?)\b', re.I),
        (
            'The assignment encompasses enterprise systems requirement analysis, secure cloud-native application engineering, and the deployment of a scalable enterprise digital database.',
            'Key technical requirements involve Enterprise Software Architecture Solutions, Relational Database Engineering & Cloud Integration, quality assurance, and integration with automated operational monitoring systems.',
            'software and IT solutions project',
            'Software & IT Solutions Project'
        )
    ),
    # 12. Urban Infrastructure, Municipal Planning & Construction
    (
        'urban',
        re.compile(r'\b(urban planning|municip\w*|town planning|\bcities\b|\bcity\b|housing|smart city|civic infrastructure|slums?|\bwards?\b|property tax|construction|civil works?|buildings?|structures?|toilet blocks?)\b', re.I),
        (
            'The assignment encompasses comprehensive municipal asset mapping, high-precision urban infrastructure surveys, and the deployment of an enterprise civic digital database.',
            'Key technical requirements involve Urban Spatial Planning Solutions, Municipal Cadastre & Infrastructure Engineering, quality assurance, and integration with municipal governance monitoring systems.',
            'urban infrastructure project',
            'Urban Infrastructure Project'
        )
    ),
    # 13. Telecommunications & Fiber Networks
    (
        'telecom',
        re.compile(r'\b(telecom\w*|optical fibers?|\bofc\b|fiber optic|broadband|wireless networks?|telephony)\b', re.I),
        (
            'The assignment encompasses telecommunication corridor data acquisition, optical fiber route surveys, and the deployment of an enterprise network GIS database.',
            'Key technical requirements involve Telecommunication Network Engineering, Fiber Asset Inventory & Spatial Management, quality assurance, and integration with telecommunication operations monitoring systems.',
            'telecommunication infrastructure project',
            'Telecommunication Infrastructure Project'
        )
    ),
    # 14. Mining & Geological Resources
    (
        'mining',
        re.compile(r'\b(mining|minerals?|geology|geological|quarr\w*)\b', re.I),
        (
            'The assignment encompasses mineral terrain data acquisition, high-precision geological mapping surveys, and the deployment of an enterprise geological spatial database.',
            'Key technical requirements involve Geological Spatial Modeling Solutions, Mineral Asset & Terrain Engineering, quality assurance, and integration with statutory mining compliance monitoring systems.',
            'mining and geological resources project',
            'Mining & Geological Resources Project'
        )
    ),
    # 15. Ports, Maritime & Coastal
    (
        'maritime',
        re.compile(r'\b(ports?|maritime|harbors?|harbours?|jetties|jetty|inland waterways?|bathymetr\w*)\b', re.I),
        (
            'The assignment encompasses bathymetric field data acquisition, coastal and maritime corridor surveys, and the deployment of an enterprise maritime spatial database.',
            'Key technical requirements involve Hydrographic & Coastal Asset Engineering, Marine Geodatabase Solutions, quality assurance, and integration with vessel traffic and port monitoring systems.',
            'maritime and port infrastructure project',
            'Maritime & Port Infrastructure Project'
        )
    ),
    # 16. Financial, Audit & Governance Advisory
    (
        'governance',
        re.compile(r'\b(financ\w*|audits?|governance|\btax\b|taxes|accounting|advisory services?|macro economic|trade finance)\b', re.I),
        (
            'The assignment encompasses institutional data collection, systematic financial and operational process reviews, and the deployment of an enterprise governance tracking database.',
            'Key technical requirements involve Financial Governance Advisory Solutions, Operational Process & Systems Engineering, quality assurance, and integration with statutory governance monitoring systems.',
            'financial and governance advisory project',
            'Financial & Governance Advisory Project'
        )
    ),
]


def generate_project_technical_scope(
    title: Optional[str] = "",
    description: Optional[str] = "",
    project_sector: Optional[str] = "",
    department: Optional[str] = "",
    keywords_str: Optional[str] = "",
    scope_of_work: Optional[str] = ""
) -> Tuple[str, str, str]:
    """
    Dynamically generates the 2-sentence project technical scope according to the project/tender,
    without including any client information, tender IDs, budgets, deadlines, or locations.

    Strict format:
    Sentence 1: The assignment encompasses {act1}, {act2}, and {act3}.
    Sentence 2: Key technical requirements involve {req1}, {req2}, quality assurance, and {req3}.

    Returns:
    (technical_scope_paragraph, sector_phrase, sector_title)
    """
    text = f"{title or ''} {project_sector or ''} {scope_of_work or ''} {description or ''} {keywords_str or ''}".lower()
    for domain_id, regex, (s1, s2, phrase, sec_title) in PROJECT_TECHNICAL_SCOPE_PATTERNS:
        if regex.search(text):
            return f"{s1} {s2}", phrase, sec_title

    # Default fallback adhering strictly to the exact same format
    s1 = "The assignment encompasses comprehensive field data acquisition, digital technical surveys, and the deployment of an enterprise digital spatial database."
    s2 = "Key technical requirements involve Enterprise Technology Solutions, Digital Engineering & Geodatabase Architecture, quality assurance, and integration with public infrastructure monitoring systems."
    return f"{s1} {s2}", "technology and infrastructure project", "Technology & Infrastructure Project"


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
    _, phrase, title_sec = generate_project_technical_scope(
        title=title,
        project_sector=project_sector,
        department=department,
        keywords_str=keywords_str
    )
    return title_sec, phrase


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

def clean_project_title(raw_title: Optional[str]) -> str:
    """Clean and standardize tender/project title for email body and subject line."""
    if not raw_title:
        return "Technology & Geospatial Infrastructure Project"
    t = raw_title.strip()
    if t.startswith("[") and t.endswith("]"):
        t = t[1:-1].strip()
    # Remove leading procurement labels e.g. LOAN-4553 CAM:, TA-9626 IND:, IFB No., RFP, NIT
    t = re.sub(r'^(LOAN|GRANT|TA|IFB|RFP|NIT|Tender\s*No\.?)\s*[-#A-Za-z0-9/]+(\s+[A-Za-z]{3})?:\s*', '', t, flags=re.I)
    t = re.sub(r'^Estimate\s+No\.?\s*[-#A-Za-z0-9/\s]+:\s*', '', t, flags=re.I)
    # If there's a Sub Head / SH, take the primary work description
    sub_head_match = re.search(r'(?:Sub\s*Head|SH[:\s-]+)\s*(.+)', t, re.I)
    if sub_head_match:
        t = sub_head_match.group(1).strip()
    # Remove embedded tender ID or notice reference tags
    t = re.sub(r'\s*\((?:Tender\s*ID|Ref(?:erence)?\s*No\.?|Package\s*No\.?|Notice\s*No\.?)\s*:[^)]*\)', '', t, flags=re.I)
    # Remove trailing package/consultancy codes e.g. (E-055197-001)
    t = re.sub(r'\s*\([A-Za-z0-9_-]+\)\s*$', '', t)
    t = t.strip("'\" \t\r\n")
    return t or "Technology & Geospatial Infrastructure Project"


def build_collaboration_email_text(
    project_name: Optional[str] = None,
    project_overview: Optional[str] = None,
    state_name: Optional[str] = None,
    is_adb: bool = False,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    sector_phrase: Optional[str] = None,
    technical_scope_paragraph: Optional[str] = None
) -> str:
    """Build the clean plain text initial collaboration outreach email with dynamic technical scope and project title."""
    s_info = resolve_sender_details(is_adb=is_adb, sender_email=sender_email, sender_name=sender_name)
    resolved_name = s_info["name"]
    clean_title = clean_project_title(project_name)

    if not technical_scope_paragraph:
        technical_scope_paragraph, derived_phrase, _ = generate_project_technical_scope(
            title=project_name,
            description=project_overview,
            project_sector=sector_phrase
        )
        if not sector_phrase:
            sector_phrase = derived_phrase

    return f"""Dear Team,

Greetings from GISFY Private Limited, India.

We are an ISO-certified technology company specialising in Geographic Information Systems (GIS), WebGIS, Artificial Intelligence and Machine Learning (AI/ML), data analytics, Management Information Systems (MIS), cloud solutions, and digital transformation.

We are currently exploring a potential Joint Venture (JV) / Consortium partnership with your organisation to collaborate and work together for the following project:

{technical_scope_paragraph}

Considering your organisation's expertise and experience, we believe there are strong synergies for mutual collaboration in the joint execution and implementation of this project.

If your organisation is interested in exploring this partnership opportunity, we kindly request you to share the following preliminary documents for our mutual evaluation:

Company Profile – Highlighting technical capabilities, core competencies, and areas of expertise.
Company Registration Certificate – Valid documentation confirming legal registration.
Tax Registration Certificate – Applicable tax registration documents.
CVs of Key Experts – Profiles of qualified professionals and technical specialists.
Relevant Project Experience – Overview of similar completed or ongoing projects.

Upon receiving and reviewing these details, we would be pleased to schedule an introductory discussion and share a draft Joint Venture / Consortium Agreement for your review and mutual consideration.

We look forward to your positive response and the opportunity to establish a mutually beneficial partnership.

Thanks & Regards,
{resolved_name}
GISFY Private Limited, Ground Floor, DSL Abacus IT Park,
Uppal, Hyderabad, Telangana – 500039, India
Mobile: +91 90631 20678
Website : www.gisfy.co.in"""

def build_collaboration_email_html(
    project_name: Optional[str] = None,
    project_overview: Optional[str] = None,
    state_name: Optional[str] = None,
    is_adb: bool = False,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    subject_line: Optional[str] = None,
    sector_phrase: Optional[str] = None,
    technical_scope_paragraph: Optional[str] = None,
    logo_src: Optional[str] = None
) -> str:
    """Build clean executive HTML email strictly containing only letter, project title, and authentic PNG GISFY logo."""
    if not logo_src:
        logo_src = "{{GISFY_LOGO_SRC}}"
    s_info = resolve_sender_details(is_adb=is_adb, sender_email=sender_email, sender_name=sender_name)
    resolved_name = s_info["name"]
    clean_title = clean_project_title(project_name)

    if not technical_scope_paragraph:
        technical_scope_paragraph, derived_phrase, _ = generate_project_technical_scope(
            title=project_name,
            description=project_overview,
            project_sector=sector_phrase
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
    <p style="margin: 0 0 4px 0; padding: 0; font-size: 15px; font-weight: 700; color: #0f172a; line-height: 1.4; text-align: left;">{resolved_name}</p>
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
            scope_work = getattr(getattr(tender, "adb_details", None), "scope_of_work", "")
            scope_para, sec_phrase, sec_title = generate_project_technical_scope(
                title=tender.title,
                description=tender.description or project_overview,
                project_sector=proj_sec,
                department=tender.department,
                keywords_str=kw_str,
                scope_of_work=scope_work
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
                sector_phrase=sec_phrase,
                technical_scope_paragraph=scope_para
            )
            body_html = build_collaboration_email_html(
                project_name=tender.title,
                project_overview=project_overview,
                state_name=state_name,
                is_adb=is_adb,
                sender_name=s_info["name"],
                sender_email=s_info["email"],
                subject_line=subject,
                sector_phrase=sec_phrase,
                technical_scope_paragraph=scope_para
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
        - Ensures From: GISFY Support <support@gisfy.co.in>, Reply-To: support@gisfy.co.in
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
            cc_email=None,
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
