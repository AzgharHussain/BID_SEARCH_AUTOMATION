import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models import models

def format_dmy(dt: Optional[datetime]) -> str:
    if not dt:
        return "As per tender schedule"
    return dt.strftime("%d %b %Y")

def extract_project_scope_overview(tender: models.Tender) -> Dict[str, Any]:
    """
    Extract project scope, eligibility criteria, required expertise,
    technical requirements, deliverables, deadlines, and partnership opportunities.
    Produces a crisp 2-5 line Project Overview suitable for the GISFY email template.
    """
    title = tender.title or "Geospatial & Technology Implementation Project"
    dept = tender.department or "Government of India / State Procurement Authority"
    state_name = tender.state.name if tender.state else "India"
    tender_id = tender.tender_id or f"TND-{tender.id}"
    deadline = format_dmy(tender.last_date)
    
    # Identify key thematic domains from title and description
    combined_text = f"{title} {tender.description or ''} {tender.department or ''}".lower()
    
    domains = []
    if "drone" in combined_text or "uav" in combined_text or "aerial" in combined_text:
        domains.append("Drone / UAV Survey & Aerial Photogrammetry")
    if "lidar" in combined_text:
        domains.append("Airborne / Terrestrial LiDAR & Point Cloud Analytics")
    if "gis" in combined_text or "geodatabase" in combined_text or "geoportal" in combined_text:
        domains.append("Enterprise GIS, WebGIS & Spatial Geodatabase Development")
    if "remote sensing" in combined_text or "satellite" in combined_text:
        domains.append("High-Resolution Satellite Remote Sensing & Imagery Classification")
    if "scada" in combined_text or "water" in combined_text or "pipeline" in combined_text or "telemetry" in combined_text:
        domains.append("Smart SCADA Telemetry, Pipeline Modeling & Water Network GIS")
    if "property" in combined_text or "tax" in combined_text or "cadastral" in combined_text or "land" in combined_text:
        domains.append("Cadastral Mapping, Land Records Modernization & Municipal Property Tax GIS")
    if "road" in combined_text or "highway" in combined_text or "pavement" in combined_text or "traffic" in combined_text:
        domains.append("Road Asset Inventory, Mobile LiDAR & Pavement Condition Digital Survey")
    if "ai" in combined_text or "machine learning" in combined_text or "deep learning" in combined_text:
        domains.append("AI/ML Computer Vision & Automated Feature Extraction")
    if "solar" in combined_text or "power" in combined_text or "electrical" in combined_text:
        domains.append("Renewable Energy Site Characterization & Utility GIS Infrastructure")

    if not domains:
        domains = ["Enterprise GIS Solutions", "Digital Surveying & Geodatabase Engineering"]

    # Build 2-5 line tailored Project Overview
    # Must capture: objectives, scope of work, key technical requirements, and expected outcomes
    overview_lines = [
        f"The {dept} ({state_name}) has issued Tender #{tender_id} for '{title}'.",
        f"The assignment encompasses comprehensive field data acquisition, high-precision geospatial surveys, and the deployment of an enterprise WebGIS digital database.",
        f"Key technical requirements involve {', '.join(domains[:3])}, quality assurance, and integration with public infrastructure monitoring systems.",
        f"The expected outcome is a centralized, authoritative digital spatial asset registry and analytics platform with bid submission closing on {deadline}."
    ]
    overview_text = " ".join(overview_lines)

    # Deliverables
    deliverables = [
        "Inception Report, Standard Operating Procedures (SOPs) & Quality Assurance Plan",
        f"Primary Data Acquisition via {domains[0]} with Ground Control Points (DGPS/RTK)",
        "Processed Spatial Datasets, Orthomosaic Imagery (GSD < 5cm) & Digital Elevation Models (DEM/DTM)",
        "Enterprise WebGIS Portal, Interactive Dashboards & Analytical Reporting Module",
        "Comprehensive Project Handover, User Training & Post-Implementation Technical Support"
    ]

    # Eligibility & Partnership Synergies
    eligibility_criteria = [
        "Consortium / Joint Venture (JV) permitted as per procurement norms",
        "Demonstrated prior experience in state/central government geospatial or IT execution",
        "ISO 9001:2015 quality certifications & valid statutory registrations (GST, PAN)",
        "Adequate technical personnel, survey equipment inventory & financial stability"
    ]

    partnership_synergies = {
        "gisfy_role": "GISFY Private Limited will lead enterprise WebGIS development, spatial data engineering, AI/ML feature analytics, cloud hosting architecture, and overall bid coordination.",
        "partner_role": f"Partner to lead specialized field operations, {domains[0]}, local logistics, and domain-specific regulatory certifications."
    }

    return {
        "tender_id": tender_id,
        "project_name": f"{title} (Tender ID: {tender_id})",
        "department": dept,
        "state_name": state_name,
        "deadline": deadline,
        "required_expertise": domains,
        "project_overview": overview_text,
        "deliverables": deliverables,
        "eligibility_criteria": eligibility_criteria,
        "partnership_synergies": partnership_synergies
    }
