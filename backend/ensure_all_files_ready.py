"""
Engine for authentic document generation (PDFs, BOQ Spreadsheets, and ZIP Bundles).
Generates comprehensive, multi-page official government procurement documents tailored
to the exact domain, department, technical scope, and financial schedules.
"""

import os
import zipfile
from pathlib import Path
from datetime import datetime

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # PyMuPDF

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def get_domain_profile(title: str, kw_name: str, dept: str, desc: str = ""):
    """Analyze title and keywords to produce authentic, domain-specific engineering & procurement profiles."""
    title = str(title or "")
    kw_name = str(kw_name or "")
    dept = str(dept or "")
    desc = str(desc or "")
    t_lower = (title + " " + kw_name + " " + dept + " " + desc).lower()
    
    if any(k in t_lower for k in ["property tax", "urban local", "ulb", "asset mapping", "door-to-door", "municipal"]):
        return {
            "key": "URBAN_GIS_TAX",
            "domain_title": "Urban Property Tax Geospatial Survey & Municipal Asset Geodatabase",
            "scope_desc": (
                "The competent municipal authority requires turnkey execution of high-resolution drone photogrammetry, "
                "continuous GNSS Ground Control Points (GCP) network establishment, 100% door-to-door spatial property tax "
                "assessment, unique property identification number (UPIN) integration, and enterprise web-GIS municipal portal deployment. "
                "The objective is complete property revenue saturation, unauthorized construction detection, and seamless integration with the state municipal revenue billing gateway."
            ),
            "boq_items": [
                ("1.01", "Establishment of DGPS Ground Control Points (GCP) network linked to Survey of India CORS network", 45, "Points", 12500),
                ("1.02", "High-Resolution Drone Aerial Photogrammetric Survey (5 cm GSD, True Orthophoto in GeoTIFF/ECW format)", 180, "Sq. Km", 18500),
                ("1.03", "3D Digital Surface Model (DSM) & Digital Terrain Model (DTM) extraction with 0.5m contour interval", 180, "Sq. Km", 8000),
                ("1.04", "Base Map Vectorization & Building Footprint Digitization with rooftop material and floor classification", 125000, "Properties", 45),
                ("1.05", "100% Door-to-Door Field Property Geospatial Assessment & Socio-economic Geo-tagging via Mobile GIS App", 125000, "Properties", 115),
                ("1.06", "Unique Property Identification Number (UPIN / BUID) QR-Code Plate Generation & Field Fixing", 125000, "Units", 38),
                ("1.07", "Integration of Spatial Geodatabase with Municipal CDMA / Revenue Billing Software & Tax Demand Registers", 1, "Lump-sum", 2850000),
                ("1.08", "Enterprise Web GIS Public Portal & Municipal Administrative Dashboard Development (PostgreSQL/PostGIS, GeoServer)", 1, "System", 3600000),
                ("1.09", "Comprehensive 3-Year On-site Technical Operations, Software Maintenance & Field Updates (FMS)", 36, "Months", 125000)
            ],
            "turnover_cr": "15.00",
            "past_exp": "Successfully completed at least three GIS-based property tax / urban mapping projects for State ULBs/Smart Cities.",
            "lead_expert": "M.Tech Geoinformatics / Urban Planning with 10+ years experience in Municipal WebGIS."
        }
    
    elif any(k in t_lower for k in ["svamitva", "cadastral", "abadi", "land record", "revenue settlement"]):
        return {
            "key": "DRONE_CADASTRAL",
            "domain_title": "Large-Scale Digital Cadastral Mapping & SVAMITVA Drone Survey",
            "scope_desc": (
                "Turnkey large-scale digital cadastral surveying using DGCA-certified survey drones, RTK/PPK GNSS baseline adjustment, "
                "village Abadi boundary demarcation, ground truthing, public objection resolution, and automated Land Record (RoR) "
                "database generation for issuing official Digital Property Cards (Gharoni) adhering to Survey of India SVAMITVA guidelines."
            ),
            "boq_items": [
                ("1.01", "Survey of India Empaneled Drone Flight Survey with RTK/PPK GNSS receivers (1:500 scale precision)", 250, "Sq. Km", 22000),
                ("1.02", "DGPS GCP monumentation and CORS baseline adjustment", 60, "Points", 11000),
                ("1.03", "Orthorectified Mosaic processing with sub-5cm RMSE horizontal positional accuracy", 250, "Sq. Km", 9500),
                ("1.04", "Large-Scale Digital Cadastral Boundary Feature Extraction and Village Abadi demarcation", 85000, "Parcels", 65),
                ("1.05", "Ground Truthing & Public Objection Resolution Support with Revenue Department officials", 120, "Villages", 48000),
                ("1.06", "Final Land Record (RoR) & Digital Property Card (Gharoni) Database preparation", 85000, "Records", 32),
                ("1.07", "Web-enabled Cadastral Land Information Management System (LIMS) deployment", 1, "System", 3200000),
                ("1.08", "Operations, technical handover and capacity building training for Revenue staff", 1, "Lump-sum", 1850000)
            ],
            "turnover_cr": "20.00",
            "past_exp": "Empaneled with Survey of India or proven experience executing SVAMITVA village mapping.",
            "lead_expert": "M.Sc / M.Tech Surveying Engineering with DGCA remote pilot license & 8+ years experience."
        }

    elif any(k in t_lower for k in ["lidar", "pavement", "road asset", "highway", "traffic", "pwd"]):
        return {
            "key": "ROAD_LIDAR_PMS",
            "domain_title": "Mobile LiDAR Road Asset Inventory & Automated Pavement Condition Survey",
            "scope_desc": (
                "Comprehensive road asset inventory and automated pavement distress condition survey using Mobile LiDAR Scanning (MLS) "
                "and calibrated 360-degree high-definition spherical cameras. Turnkey development of an enterprise Pavement Management "
                "System (PMS) and GIS geodatabase strictly conforming to Indian Roads Congress (IRC) specifications."
            ),
            "boq_items": [
                ("1.01", "Mobile LiDAR Scanning (MLS) & 360-degree High-Definition Panoramic Video Road Survey", 1200, "Lane-Km", 6800),
                ("1.02", "Automated Pavement Distress & Roughness Index (IRI) Evaluation using Computer Vision", 1200, "Lane-Km", 4500),
                ("1.03", "3D Road Asset Feature Extraction (Signboards, Streetlights, Bridges, Culverts, Footpaths)", 1200, "Lane-Km", 5200),
                ("1.04", "Road Network Spatial Geodatabase Creation adhering to IRC:SP:19 and IRC:SP:84 guidelines", 1, "Job", 2400000),
                ("1.05", "Enterprise Pavement Management System (PMS) Web Portal & GIS Decision Support System", 1, "System", 3800000),
                ("1.06", "Periodic Maintenance Schedule Formulation and Priority Defect Matrix Report", 1, "Job", 1600000),
                ("1.07", "Cloud Server Hosting, Annual Data Updates and Multi-Year Facility Management Support", 24, "Months", 110000)
            ],
            "turnover_cr": "18.00",
            "past_exp": "Minimum 2,500 lane-km of Mobile LiDAR road survey for NHAI, State PWD, or municipal corporations.",
            "lead_expert": "M.Tech Transportation / Highway Engineering with 8+ years in Mobile LiDAR & PMS modeling."
        }

    elif any(k in t_lower for k in ["command", "cctv", "anpr", "traffic control", "smart city", "iccc"]):
        return {
            "key": "SMART_TRAFFIC_COMMAND",
            "domain_title": "AI Integrated Traffic Command & Control Center (ICCC) & Spatial Surveillance",
            "scope_desc": (
                "Establishment of an AI-Powered Integrated Traffic & Urban Infrastructure Command and Control Center (ICCC). "
                "Encompasses high-density IP CCTV integration, AI video analytics (ANPR, Red-Light Violation, Speed Enforcement), "
                "Adaptive Traffic Control Systems (ATCS), real-time spatial GIS digital twin visualization, and high-availability cloud data center hosting."
            ),
            "boq_items": [
                ("1.01", "Integrated Command and Control Center (ICCC) Video Wall Display System & Workstation Infrastructure", 1, "System", 8500000),
                ("1.02", "AI-Powered Video Analytics Software (ANPR, Red Light Violation, Congestion Heatmaps)", 250, "Channels", 32000),
                ("1.03", "Adaptive Traffic Control System (ATCS) Junction Controller Supply & Fiber Interface", 45, "Junctions", 280000),
                ("1.04", "Real-Time Spatial GIS Traffic Visualization Engine & Digital Twin Dashboard", 1, "Platform", 4800000),
                ("1.05", "Cloud Data Center & Disaster Recovery High-Availability Infrastructure Setup (SLA 99.9%)", 1, "System", 6500000),
                ("1.06", "Underground Optical Fiber Cable (OFC) Network Splicing, Testing and Termination", 65, "Km", 125000),
                ("1.07", "24x7 Operations, Control Room Staffing and Multi-Year Facility Management", 36, "Months", 240000)
            ],
            "turnover_cr": "30.00",
            "past_exp": "Demonstrated execution of Smart City ICCC or statewide AI video surveillance network.",
            "lead_expert": "B.Tech / M.Tech Computer Science / Electronics with 12+ years in Smart City systems integration."
        }

    elif any(k in t_lower for k in ["water resources", "hydro", "flood", "river", "irrigation", "telemetry"]):
        return {
            "key": "WATER_RESOURCES_SCADA",
            "domain_title": "River Basin Hydro-Meteorological Telemetry Sensor Network & GIS Flood Simulation",
            "scope_desc": (
                "Turnkey design, supply, installation, testing and commissioning of automated hydro-meteorological telemetry stations, "
                "radar water level sensors, automated rain gauges (ARG), and real-time SCADA IoT gateway infrastructure. "
                "Coupled with 1D/2D hydrodynamic flood simulation models and web-GIS early warning emergency decision dashboards."
            ),
            "boq_items": [
                ("1.01", "Telemetry-enabled Automated Weather Stations (AWS) & Rain Gauges (ARG) with Solar Power", 40, "Stations", 340000),
                ("1.02", "Water Level Radar Sensors & Ultrasonic Stream Gauging Telemetry Equipment", 30, "Stations", 420000),
                ("1.03", "Real-Time SCADA Remote Terminal Units (RTU) & GSM/GPRS IoT Gateway Units", 70, "Units", 185000),
                ("1.04", "1D/2D Hydrodynamic River Basin Flood Simulation Engine & Inundation Mapping Module", 1, "System", 6200000),
                ("1.05", "Web GIS Early Warning Dashboard & Citizen SMS Alert Dissemination System", 1, "Platform", 3800000),
                ("1.06", "Bathymetric Cross-Section Hydrographic Survey of Vulnerable River Reaches", 180, "River-Km", 14500),
                ("1.07", "Annual Calibration, Sensor Maintenance, Data Assurance and 24x7 Flood Cell Support", 36, "Months", 165000)
            ],
            "turnover_cr": "22.00",
            "past_exp": "Proven track record in river basin telemetry, dam SCADA, or National Hydrology Project (NHP) contracts.",
            "lead_expert": "M.Tech Hydrology / Water Resources / Instrumentation with 10+ years in telemetry networks."
        }

    elif any(k in t_lower for k in ["forest", "wildlife", "canopy", "vegetation", "environment"]):
        return {
            "key": "FOREST_WILDLIFE",
            "domain_title": "Satellite Forest Canopy Density Monitoring & Wildlife Corridor Spatial Mapping",
            "scope_desc": (
                "Multi-temporal satellite remote sensing imagery analysis, automated NDVI forest canopy density classification, "
                "wildlife migratory corridor tracking, forest boundary demarcation using DGPS pillars, and mobile GIS field "
                "patrol enforcement applications conforming to Forest Survey of India (FSI) standards."
            ),
            "boq_items": [
                ("1.01", "Multi-temporal Sentinel-2 & High-Resolution Satellite Imagery Acquisition & Ortho-processing", 12, "Seasons", 320000),
                ("1.02", "Automated NDVI Forest Canopy Density Modeling & Forest Type Classification (FSI Standards)", 8500, "Sq. Km", 480),
                ("1.03", "DGPS Demarcation of Reserved Forest Boundaries and Geo-tagging of Boundary Pillars", 2400, "Pillars", 1850),
                ("1.04", "Wildlife Migration Corridor Spatial Tracking & Human-Wildlife Conflict Hotspot Mapping", 1, "Study", 2800000),
                ("1.05", "Mobile Field Patrol & Forest Fire Geo-Reporting Application (Android/iOS with offline GIS)", 1, "System", 3200000),
                ("1.06", "Forest Carbon Stock Assessment & Biomass Estimation Spatial Geodatabase", 1, "System", 3500000),
                ("1.07", "Capacity Building Training for Forest Range Officers & 2-Year Cloud Maintenance Support", 24, "Months", 120000)
            ],
            "turnover_cr": "12.00",
            "past_exp": "Completed at least two remote sensing forestry monitoring projects for State Forest Departments.",
            "lead_expert": "M.Sc Forestry / Remote Sensing with 8+ years experience in environmental GIS."
        }

    elif any(k in t_lower for k in ["ssdi", "spatial data", "geoportal", "ogc", "elcot", "state spatial"]):
        return {
            "key": "SPATIAL_INFRASTRUCTURE",
            "domain_title": "State Spatial Data Infrastructure (SSDI) & Multi-Departmental WebGIS Portal",
            "scope_desc": (
                "Establishment, expansion, hosting, and facility management of the State Spatial Data Infrastructure (SSDI). "
                "Encompasses OGC-compliant Web Map Services (WMS, WFS, WCS, CSW), statewide geospatial cataloging, "
                "cross-departmental spatial data standard harmonization, and high-availability cloud geo-portal operations."
            ),
            "boq_items": [
                ("1.01", "State Spatial Data Infrastructure (SSDI) Core Portal Architecture & Metadata Catalog (OGC CSW)", 1, "Platform", 7500000),
                ("1.02", "High-Resolution Multi-Spectral Satellite Imagery Hosting & OGC Compliant WMS/WFS/WCS Services", 1, "System", 5500000),
                ("1.03", "Cross-Departmental Spatial Data Standardization, ETL Pipelines & Schema Harmonic Alignment", 28, "Departments", 185000),
                ("1.04", "Cloud-Native Distributed Spatial Database (PostGIS Cluster) with Geo-Replication", 1, "Cluster", 4200000),
                ("1.05", "Decision Support GIS Application Modules (Disaster Management, Industrial Land Bank, Utilities)", 4, "Modules", 1800000),
                ("1.06", "API Gateway, Mobile SDK and Open Data Developer Portal", 1, "System", 2600000),
                ("1.07", "3-Year Enterprise SLA Technical Support, Cybersecurity Audits (CERT-In) and Maintenance", 36, "Months", 195000)
            ],
            "turnover_cr": "25.00",
            "past_exp": "Implementation of State Spatial Data Infrastructure, National Geospatial portal, or state NSDI node.",
            "lead_expert": "Enterprise Enterprise GIS Solutions Architect with 12+ years in OGC standards and cloud GIS."
        }

    else:
        return {
            "key": "GENERAL_GEOSPATIAL",
            "domain_title": "Turnkey Geospatial Solutions, Digital Survey & IT Infrastructure",
            "scope_desc": (
                "Turnkey execution of specialized engineering survey, spatial remote sensing analysis, enterprise database integration, "
                "and web-enabled decision support systems adhering to official state e-procurement standards and statutory guidelines."
            ),
            "boq_items": [
                ("1.01", "Inception Planning, High-Accuracy DGPS Ground Survey & CORS Geo-referencing", 1, "Job", 1800000),
                ("1.02", "Drone / Aerial Remote Sensing Imagery Acquisition & Photogrammetry Ortho-mosaic", 1, "Job", 3800000),
                ("1.03", "Spatial Vector Feature Extraction, Attribute Classification & Quality Verification", 1, "Job", 3200000),
                ("1.04", "Enterprise Geodatabase Architecture Design & State Portal Integration", 1, "System", 4500000),
                ("1.05", "Interactive Web GIS Dashboard Development with Spatial Query & Decision Support", 1, "Platform", 3600000),
                ("1.06", "Training, Technology Transfer, Cloud Infrastructure Setup & 1-Year AMC Maintenance", 12, "Months", 110000)
            ],
            "turnover_cr": "14.00",
            "past_exp": "Demonstrated completion of complex geospatial IT solutions for government departments or PSUs.",
            "lead_expert": "Senior Geospatial Systems Consultant with 10+ years experience in turnkey surveying and GIS."
        }


def make_authentic_pdf(target_path, tender, state_name, kw_name, file_name):
    """
    Generate an authentic, comprehensive 4-to-5-page official government tender / RFP document
    with rich technical scope, eligibility criteria, schedules, and official gazette formatting.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open()
    
    title_text = getattr(tender, "title", str(tender))
    tender_id = getattr(tender, "tender_id", "REF-2026")
    dept = getattr(tender, "department", "Department of Information Technology & Municipal Infrastructure")
    desc = getattr(tender, "description", "")
    
    pub_date = getattr(tender, "published_date", None)
    pub_str = pub_date.strftime("%d %b %Y") if hasattr(pub_date, "strftime") else "14 Oct 2026"
    
    due_date = getattr(tender, "last_date", None)
    due_str = due_date.strftime("%d %b %Y, 15:00 hrs") if hasattr(due_date, "strftime") else "29 Oct 2026, 15:00 hrs"
    
    state_upper = str(state_name).upper()
    profile = get_domain_profile(title_text, kw_name, dept, desc)
    is_tech_spec = any(w in file_name.lower() for w in ["technical", "scope", "specification", "rfp"])
    
    # ---------------- PAGE 1: OFFICIAL GAZETTE & NOTICE INVITING TENDER (NIT) ----------------
    p1 = doc.new_page(width=595, height=842)
    
    # Top banner header
    p1.draw_rect(fitz.Rect(36, 36, 559, 102), color=(0.08, 0.12, 0.32), fill=(0.08, 0.12, 0.32))
    p1.insert_text(fitz.Point(52, 60), f"GOVERNMENT OF {state_upper}", fontsize=13, fontname="helv", color=(1, 1, 1))
    p1.insert_text(fitz.Point(52, 77), f"OFFICIAL e-PROCUREMENT TENDER NOTIFICATION — {profile['domain_title']}", fontsize=8.5, fontname="helv", color=(0.85, 0.9, 1))
    doc_type_title = "DETAILED TECHNICAL SPECIFICATIONS & SCOPE DOCUMENT" if is_tech_spec else "NOTICE INVITING TENDER (NIT) & BIDDING DOCUMENT"
    p1.insert_text(fitz.Point(52, 94), doc_type_title, fontsize=10, fontname="helv", color=(0.95, 0.8, 0.3))
    
    # Key Tender Meta Table
    p1.draw_rect(fitz.Rect(36, 115, 559, 215), color=(0.78, 0.82, 0.9), fill=(0.96, 0.97, 1.0))
    p1.insert_text(fitz.Point(48, 134), f"Tender Reference ID: {tender_id}", fontsize=10, fontname="helv", color=(0.08, 0.12, 0.32))
    p1.insert_text(fitz.Point(340, 134), f"Portal: https://tender.{state_name.lower().replace(' ', '')}.gov.in", fontsize=8.5, fontname="helv", color=(0.3, 0.4, 0.6))
    p1.insert_text(fitz.Point(48, 152), f"Department / Authority: {dept}", fontsize=9, fontname="helv", color=(0.15, 0.15, 0.15))
    p1.insert_text(fitz.Point(48, 170), f"Published Date: {pub_str}  |  Online Bid Closing: {due_str}", fontsize=9, fontname="helv", color=(0.2, 0.2, 0.2))
    p1.insert_text(fitz.Point(48, 188), f"Tender Type: Open Competitive Global / National e-Bidding  |  Form of Contract: Turnkey Item Rate", fontsize=8.5, fontname="helv", color=(0.3, 0.3, 0.3))
    p1.insert_text(fitz.Point(48, 206), f"EMD Value: 2% of Bid Value via e-Gateway  |  Tender Document Fee: INR 10,000 + 18% GST (Non-refundable)", fontsize=8.5, fontname="helv", color=(0.1, 0.4, 0.2))
    
    # 1. Project Title & Executive Invitation
    p1.insert_text(fitz.Point(36, 240), "1. EXECUTIVE SUMMARY & INVITATION TO BID", fontsize=11, fontname="helv", color=(0.08, 0.12, 0.32))
    p1.draw_line(fitz.Point(36, 246), fitz.Point(559, 246), color=(0.08, 0.12, 0.32), width=1)
    
    exec_summary = (
        f"1.1 The Government of {state_name}, acting through {dept}, invites eligible and qualified agencies "
        f"to submit technical and financial proposals online through the official state e-procurement portal for:\n\n"
        f"\"{title_text}\"\n\n"
        f"1.2 Brief Purpose: {profile['scope_desc']}\n\n"
        f"1.3 Bidders are advised to thoroughly inspect the technical guidelines, bill of quantities (BOQ), "
        f"minimum eligibility criteria, and general condition clauses before uploading their signed and sealed proposals."
    )
    p1.insert_textbox(fitz.Rect(36, 254, 559, 395), exec_summary, fontsize=9, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # 2. Critical Dates Schedule Table
    p1.insert_text(fitz.Point(36, 415), "2. CRITICAL DATES SHEET & PROCUREMENT TIMELINES", fontsize=11, fontname="helv", color=(0.08, 0.12, 0.32))
    p1.draw_line(fitz.Point(36, 421), fitz.Point(559, 421), color=(0.08, 0.12, 0.32), width=1)
    
    dates_hdr_y = 432
    p1.draw_rect(fitz.Rect(36, dates_hdr_y, 559, dates_hdr_y + 22), color=(0.2, 0.25, 0.45), fill=(0.15, 0.2, 0.45))
    p1.insert_text(fitz.Point(46, dates_hdr_y + 15), "Milestone Event Description", fontsize=9, fontname="helv", color=(1, 1, 1))
    p1.insert_text(fitz.Point(360, dates_hdr_y + 15), "Official Schedule / Timestamp", fontsize=9, fontname="helv", color=(1, 1, 1))
    
    dates_list = [
        ("Official Portal Publication Date", pub_str),
        ("Document Download Start Date", f"{pub_str}, 10:00 hrs"),
        ("Pre-Bid Query Submission Deadline", "Within 7 Days of Portal Publication"),
        ("Pre-Bid Clarification Meeting (Hybrid/VC)", "10th Day of Publication at 11:30 hrs"),
        ("Bid Submission Start Date", f"{pub_str}, 14:00 hrs"),
        ("Online Bid Submission Due Date & Time", due_str),
        ("Technical Bid Opening Date & Time", "Next Working Day following Bid Closing at 15:30 hrs"),
        ("Financial Bid (BOQ) Opening Date", "To be notified online to technically qualified bidders")
    ]
    
    curr_y = dates_hdr_y + 22
    for idx, (evt, dt) in enumerate(dates_list):
        bg = (0.97, 0.98, 1.0) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        p1.draw_rect(fitz.Rect(36, curr_y, 559, curr_y + 20), color=(0.85, 0.88, 0.92), fill=bg)
        p1.insert_text(fitz.Point(46, curr_y + 14), evt, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
        p1.insert_text(fitz.Point(360, curr_y + 14), dt, fontsize=8.5, fontname="helv", color=(0.1, 0.15, 0.35))
        curr_y += 20
        
    # Page 1 Footer
    p1.draw_line(fitz.Point(36, 790), fitz.Point(559, 790), color=(0.75, 0.75, 0.75), width=0.5)
    p1.insert_text(fitz.Point(36, 806), f"Official Government Procurement Gazette | State: {state_name} | Tender Ref: {tender_id}", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    p1.insert_text(fitz.Point(495, 806), "Page 1 of 4", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    
    # ---------------- PAGE 2: DETAILED TECHNICAL SCOPE OF WORK ----------------
    p2 = doc.new_page(width=595, height=842)
    p2.draw_rect(fitz.Rect(36, 36, 559, 70), color=(0.08, 0.12, 0.32), fill=(0.08, 0.12, 0.32))
    p2.insert_text(fitz.Point(52, 58), f"GOVERNMENT OF {state_upper} — TECHNICAL SPECIFICATIONS", fontsize=11, fontname="helv", color=(1, 1, 1))
    
    p2.insert_text(fitz.Point(36, 95), "3. COMPREHENSIVE TECHNICAL SCOPE & ENGINEERING METHODOLOGY", fontsize=11, fontname="helv", color=(0.08, 0.12, 0.32))
    p2.draw_line(fitz.Point(36, 101), fitz.Point(559, 101), color=(0.08, 0.12, 0.32), width=1)
    
    tech_details = (
        f"3.1 Overview of Engineering Operations:\n"
        f"The selected agency shall be responsible for turnkey end-to-end execution of all technical requirements described herein. "
        f"All work must adhere strictly to National Geospatial Policy guidelines, Survey of India precision benchmarks, and relevant state standards.\n\n"
        f"3.2 Key Technical Components:\n"
        f"• Phase I — Continuous Operating Reference Station (CORS) & DGPS Network: Establishment of primary Ground Control Points (GCPs) "
        f"with Dual Frequency GNSS receivers linked to the state CORS network, achieving sub-2cm absolute spatial positioning accuracy.\n"
        f"• Phase II — High-Precision Aerial / Terrestrial Sensor Acquisition: Deployment of calibrated multi-rotor/fixed-wing survey drones "
        f"or Mobile Mapping Systems (MMS) equipped with high-resolution digital metric cameras and LiDAR sensors capable of delivering "
        f"5 cm Ground Sample Distance (GSD) orthophoto mosaics.\n"
        f"• Phase III — Vector Extraction & Feature Classification: Digitization of building footprints, road alignments, parcel boundaries, "
        f"and municipal infrastructure with structured attribute schemas conforming to national spatial data exchange standards.\n"
        f"• Phase IV — Comprehensive Field Verification & Attribute Geo-tagging: Door-to-door verification using custom mobile GIS applications "
        f"with automated GPS coordinates, photo capture, and offline cache synchronization.\n"
        f"• Phase V — Enterprise Geodatabase & Decision Support Web GIS: Development and hosting of an enterprise PostgreSQL / PostGIS spatial database "
        f"with GeoServer map services, OGC WMS/WFS interfaces, and role-based access control for department administrators."
    )
    p2.insert_textbox(fitz.Rect(36, 110, 559, 410), tech_details, fontsize=8.8, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # 3.3 Accuracy and Standards Box
    p2.insert_text(fitz.Point(36, 430), "3.3 Statutory Standards, Geodetic Accuracy & Delivery Format Requirements", fontsize=10, fontname="helv", color=(0.08, 0.12, 0.32))
    p2.draw_rect(fitz.Rect(36, 442, 559, 580), color=(0.75, 0.8, 0.9), fill=(0.96, 0.97, 1.0))
    
    specs_text = (
        "• Coordinate Reference System: WGS84 Datum / UTM Projection (conforming to state UTM Zone).\n"
        "• Horizontal Positional Accuracy: RMSE <= 5.0 cm on well-defined ground features.\n"
        "• Vertical Precision: RMSE <= 10.0 cm for Digital Surface Model (DSM) and Digital Terrain Model (DTM).\n"
        "• Orthomosaic Delivery: Uncompressed GeoTIFF and ECW format with complete pyramidal tiles.\n"
        "• Vector Delivery: ESRI File Geodatabase (.gdb) and OGC GeoPackage (.gpkg) with topological validation.\n"
        "• Attribute Data: Linked SQLite / PostgreSQL relational tables with audited integrity constraints.\n"
        "• Cloud Deployment: High-availability tier with 99.9% uptime SLA and periodic daily automated snapshots."
    )
    p2.insert_textbox(fitz.Rect(48, 452, 547, 570), specs_text, fontsize=8.8, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # 3.4 Quality Control & Inspection
    p2.insert_text(fitz.Point(36, 602), "3.4 Quality Control, Assurance & Third-Party Audit", fontsize=10, fontname="helv", color=(0.08, 0.12, 0.32))
    qc_text = (
        "The department reserves the right to appoint a Third-Party Quality Inspection Agency (TPIA) or Survey of India / "
        "State Remote Sensing Centre to validate 10% randomly selected sample plots across all deliverables. "
        "Any deliverable failing accuracy tolerances shall be resurveyed by the vendor at no additional cost to the department."
    )
    p2.insert_textbox(fitz.Rect(36, 614, 559, 690), qc_text, fontsize=8.8, fontname="helv", color=(0.2, 0.2, 0.2))
    
    p2.draw_line(fitz.Point(36, 790), fitz.Point(559, 790), color=(0.75, 0.75, 0.75), width=0.5)
    p2.insert_text(fitz.Point(36, 806), f"Official Government Procurement Gazette | State: {state_name} | Tender Ref: {tender_id}", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    p2.insert_text(fitz.Point(495, 806), "Page 2 of 4", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    
    # ---------------- PAGE 3: BIDDER ELIGIBILITY & KEY PERSONNEL CRITERIA ----------------
    p3 = doc.new_page(width=595, height=842)
    p3.draw_rect(fitz.Rect(36, 36, 559, 70), color=(0.08, 0.12, 0.32), fill=(0.08, 0.12, 0.32))
    p3.insert_text(fitz.Point(52, 58), f"GOVERNMENT OF {state_upper} — QUALIFICATION & ELIGIBILITY", fontsize=11, fontname="helv", color=(1, 1, 1))
    
    p3.insert_text(fitz.Point(36, 95), "4. MINIMUM BIDDER QUALIFICATION & TECHNICAL ELIGIBILITY CRITERIA", fontsize=11, fontname="helv", color=(0.08, 0.12, 0.32))
    p3.draw_line(fitz.Point(36, 101), fitz.Point(559, 101), color=(0.08, 0.12, 0.32), width=1)
    
    elig_intro = (
        "Bidders must meet all of the following mandatory pre-qualification conditions as on the date of bid submission. "
        "Consortiums/Joint Ventures (JV) are permitted as per the conditions stated in Section 5."
    )
    p3.insert_textbox(fitz.Rect(36, 108, 559, 138), elig_intro, fontsize=8.8, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # Eligibility Table
    tbl_y = 145
    p3.draw_rect(fitz.Rect(36, tbl_y, 559, tbl_y + 22), color=(0.2, 0.25, 0.45), fill=(0.15, 0.2, 0.45))
    p3.insert_text(fitz.Point(46, tbl_y + 15), "Criteria Category", fontsize=9, fontname="helv", color=(1, 1, 1))
    p3.insert_text(fitz.Point(180, tbl_y + 15), "Mandatory Qualification Threshold", fontsize=9, fontname="helv", color=(1, 1, 1))
    p3.insert_text(fitz.Point(440, tbl_y + 15), "Documentary Proof Required", fontsize=9, fontname="helv", color=(1, 1, 1))
    
    elig_rows = [
        ("Annual Financial Turnover", f"Average annual turnover of at least INR {profile['turnover_cr']} Crores over the last 3 financial years (FY 2023-24, 2024-25, 2025-26).", "Audited Balance Sheets & CA Certificate with UDIN"),
        ("Past Experience", profile["past_exp"], "Client Completion Certificates & Work Orders"),
        ("Quality Certifications", "Valid ISO 9001:2015, ISO 27001 (Information Security), and minimum CMMI Level 3 (Services/Dev).", "Valid Certificate Copies from Accredited Registrar"),
        ("Legal Status", "Registered Company under Indian Companies Act (or LLP) in operation for at least 5 years.", "Certificate of Incorporation & GST Registration"),
        ("Solvency Status", f"Bank Solvency Certificate for an amount not less than INR {float(profile['turnover_cr']) * 0.4:.2f} Crores from a Scheduled Commercial Bank.", "Original Bank Solvency Certificate in prescribed format"),
        ("Debarment Undertaking", "The bidder must not have been blacklisted or debarred by any Central/State Govt/PSU as on bid date.", "Notarized Affidavit on INR 100 Stamp Paper")
    ]
    
    curr_y = tbl_y + 22
    for idx, (cat, thresh, doc_proof) in enumerate(elig_rows):
        bg = (0.97, 0.98, 1.0) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        p3.draw_rect(fitz.Rect(36, curr_y, 559, curr_y + 36), color=(0.85, 0.88, 0.92), fill=bg)
        p3.insert_text(fitz.Point(46, curr_y + 14), cat, fontsize=8.5, fontname="helv", color=(0.1, 0.15, 0.35))
        p3.insert_textbox(fitz.Rect(180, curr_y + 4, 430, curr_y + 34), thresh, fontsize=7.8, fontname="helv", color=(0.15, 0.15, 0.15))
        p3.insert_textbox(fitz.Rect(440, curr_y + 4, 555, curr_y + 34), doc_proof, fontsize=7.8, fontname="helv", color=(0.25, 0.25, 0.25))
        curr_y += 36
        
    # 4.2 Key Personnel
    p3.insert_text(fitz.Point(36, curr_y + 24), "4.2 Mandatory Key Technical Personnel to be Deployed on Project", fontsize=10, fontname="helv", color=(0.08, 0.12, 0.32))
    p3.draw_line(fitz.Point(36, curr_y + 30), fitz.Point(559, curr_y + 30), color=(0.08, 0.12, 0.32), width=1)
    
    staff_y = curr_y + 38
    p3.draw_rect(fitz.Rect(36, staff_y, 559, staff_y + 20), color=(0.2, 0.25, 0.45), fill=(0.15, 0.2, 0.45))
    p3.insert_text(fitz.Point(46, staff_y + 14), "Designation / Role", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    p3.insert_text(fitz.Point(190, staff_y + 14), "Minimum Academic Qualification", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    p3.insert_text(fitz.Point(390, staff_y + 14), "Min Relevant Experience", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    
    staff_list = [
        ("Project Director / Team Leader", "M.Tech / M.Sc Remote Sensing / GIS / Civil", "12+ Years Turnkey Project Leadership"),
        ("Senior GIS Database Architect", "B.Tech / MCA with PostgreSQL/PostGIS / Oracle", "8+ Years Spatial DB Architecture"),
        ("Photogrammetry / LiDAR Specialist", "M.Tech / B.Tech Geoinformatics / Photogrammetry", "8+ Years Aerial Sensor Processing"),
        ("Field Survey & QA Lead Engineer", "Degree/Diploma Civil + DGCA Drone Pilot Cert", "6+ Years DGPS & Ground Truthing"),
        ("Full-Stack WebGIS Developer", "B.Tech Computer Science / IT (React / Python)", "5+ Years Web Map Portal Dev")
    ]
    
    s_curr = staff_y + 20
    for idx, (role, qual, exp) in enumerate(staff_list):
        bg = (0.97, 0.98, 1.0) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        p3.draw_rect(fitz.Rect(36, s_curr, 559, s_curr + 20), color=(0.85, 0.88, 0.92), fill=bg)
        p3.insert_text(fitz.Point(46, s_curr + 14), role, fontsize=8, fontname="helv", color=(0.1, 0.15, 0.35))
        p3.insert_text(fitz.Point(190, s_curr + 14), qual, fontsize=8, fontname="helv", color=(0.15, 0.15, 0.15))
        p3.insert_text(fitz.Point(390, s_curr + 14), exp, fontsize=8, fontname="helv", color=(0.2, 0.2, 0.2))
        s_curr += 20
        
    p3.draw_line(fitz.Point(36, 790), fitz.Point(559, 790), color=(0.75, 0.75, 0.75), width=0.5)
    p3.insert_text(fitz.Point(36, 806), f"Official Government Procurement Gazette | State: {state_name} | Tender Ref: {tender_id}", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    p3.insert_text(fitz.Point(495, 806), "Page 3 of 4", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    
    # ---------------- PAGE 4: MILESTONE PAYMENT SCHEDULE, SLA & SUBMISSION INSTRUCTIONS ----------------
    p4 = doc.new_page(width=595, height=842)
    p4.draw_rect(fitz.Rect(36, 36, 559, 70), color=(0.08, 0.12, 0.32), fill=(0.08, 0.12, 0.32))
    p4.insert_text(fitz.Point(52, 58), f"GOVERNMENT OF {state_upper} — DELIVERABLES & PAYMENT SCHEDULE", fontsize=11, fontname="helv", color=(1, 1, 1))
    
    p4.insert_text(fitz.Point(36, 95), "5. PROJECT DELIVERABLE MILESTONES & PROGRESS PAYMENT SCHEDULE", fontsize=11, fontname="helv", color=(0.08, 0.12, 0.32))
    p4.draw_line(fitz.Point(36, 101), fitz.Point(559, 101), color=(0.08, 0.12, 0.32), width=1)
    
    m_y = 115
    p4.draw_rect(fitz.Rect(36, m_y, 559, m_y + 22), color=(0.2, 0.25, 0.45), fill=(0.15, 0.2, 0.45))
    p4.insert_text(fitz.Point(46, m_y + 15), "Milestone", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    p4.insert_text(fitz.Point(110, m_y + 15), "Deliverable Description", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    p4.insert_text(fitz.Point(375, m_y + 15), "Target Timeline", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    p4.insert_text(fitz.Point(480, m_y + 15), "Payment (%)", fontsize=8.5, fontname="helv", color=(1, 1, 1))
    
    milestones = [
        ("M-1", "Inception Report, Project Execution Plan & Statutory Clearances", "T0 + 30 Days", "10%"),
        ("M-2", "Establishment of DGPS Ground Control Network & Raw Sensor Acquisition", "T0 + 90 Days", "20%"),
        ("M-3", "Ortho-mosaic Processing, Feature Extraction & 50% Field Verification", "T0 + 180 Days", "25%"),
        ("M-4", "100% Field Survey Completion, UPIN Geo-tagging & Database Validation", "T0 + 270 Days", "25%"),
        ("M-5", "Web GIS Portal Deployment, User Acceptance Testing (UAT) & Training", "T0 + 330 Days", "10%"),
        ("M-6", "Final Handover, Final Documentation Sign-off & Commencement of AMC", "T0 + 365 Days", "10%")
    ]
    
    m_curr = m_y + 22
    for idx, (m_code, m_desc, m_time, m_pct) in enumerate(milestones):
        bg = (0.97, 0.98, 1.0) if idx % 2 == 0 else (1.0, 1.0, 1.0)
        p4.draw_rect(fitz.Rect(36, m_curr, 559, m_curr + 22), color=(0.85, 0.88, 0.92), fill=bg)
        p4.insert_text(fitz.Point(46, m_curr + 15), m_code, fontsize=8.5, fontname="helv", color=(0.1, 0.15, 0.35))
        p4.insert_text(fitz.Point(110, m_curr + 15), m_desc, fontsize=8, fontname="helv", color=(0.15, 0.15, 0.15))
        p4.insert_text(fitz.Point(375, m_curr + 15), m_time, fontsize=8, fontname="helv", color=(0.2, 0.2, 0.2))
        p4.insert_text(fitz.Point(495, m_curr + 15), m_pct, fontsize=8.5, fontname="helv", color=(0.1, 0.4, 0.2))
        m_curr += 22
        
    # 6. Service Level Agreement (SLA) & Penalties
    p4.insert_text(fitz.Point(36, m_curr + 25), "6. SERVICE LEVEL AGREEMENT (SLA), PENALTIES & PERFORMANCE GUARANTEE", fontsize=10, fontname="helv", color=(0.08, 0.12, 0.32))
    p4.draw_line(fitz.Point(36, m_curr + 31), fitz.Point(559, m_curr + 31), color=(0.08, 0.12, 0.32), width=1)
    
    sla_box = (
        "• Performance Security (PBG): The successful bidder shall furnish a Performance Bank Guarantee equal to 5% of the total "
        "contract value within 14 days of the Letter of Award (LoA), valid until 60 days after completion of all contractual obligations.\n"
        "• Delay Liquidated Damages: If the contractor fails to deliver milestones within agreed timelines, liquidated damages of 0.5% per "
        "week of delay (or fraction thereof) shall be deducted, subject to a maximum cap of 10% of total contract value.\n"
        "• Defect Liability & Maintenance: 12 months comprehensive warranty from the date of final operational sign-off.\n"
        "• Data Security & Ownership: All raw aerial imagery, point clouds, GIS geodatabases, and field registers shall be the sole and exclusive "
        "property of the Government of " + state_name + ". The vendor shall not disclose or retain proprietary government data."
    )
    p4.insert_textbox(fitz.Rect(36, m_curr + 40, 559, m_curr + 175), sla_box, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    
    # Official Signature Box
    sig_y = m_curr + 190
    p4.draw_rect(fitz.Rect(340, sig_y, 559, sig_y + 115), color=(0.75, 0.8, 0.9), fill=(0.97, 0.98, 1.0))
    p4.insert_text(fitz.Point(355, sig_y + 22), "ISSUED FOR AND ON BEHALF OF:", fontsize=8.5, fontname="helv", color=(0.1, 0.15, 0.35))
    p4.insert_text(fitz.Point(355, sig_y + 40), f"Government of {state_name}", fontsize=9.5, fontname="helv", color=(0.08, 0.12, 0.32))
    p4.insert_text(fitz.Point(355, sig_y + 56), dept, fontsize=8, fontname="helv", color=(0.2, 0.2, 0.2))
    p4.insert_text(fitz.Point(355, sig_y + 75), "[Digitally Signed & Validated on e-Procurement Portal]", fontsize=7.5, fontname="helv", color=(0.1, 0.45, 0.2))
    p4.insert_text(fitz.Point(355, sig_y + 95), "Competent Tender Inviting Authority (TIA)", fontsize=8, fontname="helv", color=(0.3, 0.3, 0.3))
    
    p4.draw_line(fitz.Point(36, 790), fitz.Point(559, 790), color=(0.75, 0.75, 0.75), width=0.5)
    p4.insert_text(fitz.Point(36, 806), f"Official Government Procurement Gazette | State: {state_name} | Tender Ref: {tender_id}", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    p4.insert_text(fitz.Point(495, 806), "Page 4 of 4", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.45))
    
    doc.save(str(target_path))
    doc.close()
    return target_path


def make_simple_xlsx(target_path, title, tender_id, department, kw_name=""):
    """
    Generate an authentic, domain-specific official government Bill of Quantities (BOQ) spreadsheet
    with real itemized financial line items, units, quantities, rates, formulas, and multiple sheets.
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    profile = get_domain_profile(title, kw_name, department)
    
    wb = openpyxl.Workbook()
    
    # SHEET 1: Item Rate BoQ
    ws1 = wb.active
    ws1.title = "Item Rate BoQ"
    
    navy_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    sub_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    alt_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    total_fill = PatternFill(start_color="EEF2FF", end_color="EEF2FF", fill_type="solid")
    grand_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
    
    title_font = Font(name="Segoe UI", size=13, bold=True, color="0F172A")
    subtitle_font = Font(name="Segoe UI", size=10, bold=True, color="334155")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    bold_cell_font = Font(name="Segoe UI", size=9.5, bold=True, color="0F172A")
    body_font = Font(name="Segoe UI", size=9.5, color="1E293B")
    formula_font = Font(name="Segoe UI", size=10, bold=True, color="1E1B4B")
    
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    double_bottom_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="double", color="1E1B4B")
    )
    
    ws1.merge_cells("A1:H1")
    ws1["A1"] = "OFFICIAL GOVERNMENT BILL OF QUANTITIES (BOQ) — FINANCIAL SCHEDULE"
    ws1["A1"].font = title_font
    ws1["A1"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.merge_cells("A2:H2")
    ws1["A2"] = f"Tender Ref: {tender_id} | Authority: {department}"
    ws1["A2"].font = subtitle_font
    ws1["A2"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.merge_cells("A3:H3")
    ws1["A3"] = f"Work: {title}"
    ws1["A3"].font = body_font
    ws1["A3"].alignment = Alignment(horizontal="center", vertical="center")
    
    ws1.merge_cells("A4:H4")
    ws1["A4"] = "Validate Price Bid: Rates entered by bidder must include all overheads, equipment deployment, field survey, processing & software."
    ws1["A4"].font = Font(name="Segoe UI", size=8.5, italic=True, color="64748B")
    ws1["A4"].alignment = Alignment(horizontal="center", vertical="center")
    
    headers = [
        "Item No.", 
        "Item Description", 
        "Quantity", 
        "Units", 
        "Basic Estimated Rate (INR)", 
        "Basic Total Amount (INR)", 
        "GST Rate (%)", 
        "Total Amount with GST (INR)"
    ]
    
    ws1.append([])  # Row 5 empty
    ws1.append(headers)  # Row 6
    
    for col_idx in range(1, 9):
        cell = ws1.cell(row=6, column=col_idx)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws1.row_dimensions[6].height = 26
    
    start_row = 7
    items = profile["boq_items"]
    
    for idx, (code, desc, qty, unit, rate) in enumerate(items, start=start_row):
        total_cell = f"=C{idx}*E{idx}"
        gst_total_cell = f"=F{idx}*(1+G{idx}/100)"
        row_vals = [code, desc, qty, unit, rate, total_cell, 18, gst_total_cell]
        ws1.append(row_vals)
        
        row_fill = alt_fill if idx % 2 == 0 else PatternFill(fill_type=None)
        for c in range(1, 9):
            cell = ws1.cell(row=idx, column=c)
            cell.font = body_font
            cell.border = thin_border
            if row_fill.fill_type:
                cell.fill = row_fill
            if c == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c == 2:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            elif c in [3, 5, 6, 8]:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                if c == 3:
                    cell.number_format = "#,##0"
                else:
                    cell.number_format = "#,##0.00"
            elif c == 4:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c == 7:
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.number_format = "0"
        ws1.row_dimensions[idx].height = 28
        
    last_item_row = start_row + len(items) - 1
    subtotal_row = last_item_row + 1
    gst_row = subtotal_row + 1
    grand_row = gst_row + 1
    
    # Subtotal basic
    ws1.merge_cells(start_row=subtotal_row, start_column=1, end_row=subtotal_row, end_column=5)
    ws1.cell(row=subtotal_row, column=1, value="SUB-TOTAL BASIC CONTRACT VALUE (INR)").font = bold_cell_font
    ws1.cell(row=subtotal_row, column=1).alignment = Alignment(horizontal="right", vertical="center")
    subtotal_cell = ws1.cell(row=subtotal_row, column=6, value=f"=SUM(F{start_row}:F{last_item_row})")
    subtotal_cell.font = formula_font
    subtotal_cell.alignment = Alignment(horizontal="right", vertical="center")
    subtotal_cell.number_format = "#,##0.00"
    
    for c in range(1, 9):
        ws1.cell(row=subtotal_row, column=c).border = thin_border
        ws1.cell(row=subtotal_row, column=c).fill = total_fill
    ws1.row_dimensions[subtotal_row].height = 24
    
    # Total GST 18%
    ws1.merge_cells(start_row=gst_row, start_column=1, end_row=gst_row, end_column=5)
    ws1.cell(row=gst_row, column=1, value="APPLICABLE GOODS & SERVICES TAX (GST @ 18%) (INR)").font = bold_cell_font
    ws1.cell(row=gst_row, column=1).alignment = Alignment(horizontal="right", vertical="center")
    gst_sum_cell = ws1.cell(row=gst_row, column=6, value=f"=F{subtotal_row}*0.18")
    gst_sum_cell.font = formula_font
    gst_sum_cell.alignment = Alignment(horizontal="right", vertical="center")
    gst_sum_cell.number_format = "#,##0.00"
    
    for c in range(1, 9):
        ws1.cell(row=gst_row, column=c).border = thin_border
        ws1.cell(row=gst_row, column=c).fill = total_fill
    ws1.row_dimensions[gst_row].height = 24
    
    # Grand Total
    ws1.merge_cells(start_row=grand_row, start_column=1, end_row=grand_row, end_column=5)
    ws1.cell(row=grand_row, column=1, value="TOTAL ESTIMATED TENDER VALUE INCLUSIVE OF ALL TAXES (INR)").font = Font(name="Segoe UI", size=10.5, bold=True, color="0F172A")
    ws1.cell(row=grand_row, column=1).alignment = Alignment(horizontal="right", vertical="center")
    grand_sum_cell = ws1.cell(row=grand_row, column=6, value=f"=F{subtotal_row}+F{gst_row}")
    grand_sum_cell.font = Font(name="Segoe UI", size=11, bold=True, color="1E1B4B")
    grand_sum_cell.alignment = Alignment(horizontal="right", vertical="center")
    grand_sum_cell.number_format = "#,##0.00"
    
    grand_total_col8 = ws1.cell(row=grand_row, column=8, value=f"=F{grand_row}")
    grand_total_col8.font = Font(name="Segoe UI", size=11, bold=True, color="1E1B4B")
    grand_total_col8.alignment = Alignment(horizontal="right", vertical="center")
    grand_total_col8.number_format = "#,##0.00"
    
    for c in range(1, 9):
        ws1.cell(row=grand_row, column=c).border = double_bottom_border
        ws1.cell(row=grand_row, column=c).fill = grand_fill
    ws1.row_dimensions[grand_row].height = 28
    
    ws1.column_dimensions['A'].width = 11
    ws1.column_dimensions['B'].width = 68
    ws1.column_dimensions['C'].width = 13
    ws1.column_dimensions['D'].width = 14
    ws1.column_dimensions['E'].width = 24
    ws1.column_dimensions['F'].width = 26
    ws1.column_dimensions['G'].width = 13
    ws1.column_dimensions['H'].width = 28
    
    # SHEET 2: Milestone Payment Schedule
    ws2 = wb.create_sheet(title="Milestone Schedule")
    ws2["A1"] = "PROJECT DELIVERABLE MILESTONES & DISBURSEMENT PERCENTAGES"
    ws2["A1"].font = title_font
    
    m_headers = ["Milestone", "Deliverable Scope", "Timeline", "Payment Share (%)", "Cumulative (%)"]
    ws2.append([])
    ws2.append(m_headers)
    for c in range(1, 6):
        cell = ws2.cell(row=3, column=c)
        cell.fill = navy_fill
        cell.font = header_font
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    m_rows = [
        ("M-1", "Inception Report, Project Quality Plan & Statutory Clearances", "T0 + 30 Days", 10, 10),
        ("M-2", "DGPS Ground Control Network, Flight Survey & Raw Sensor Verification", "T0 + 90 Days", 20, 30),
        ("M-3", "Ortho-mosaic Processing, Feature Extraction & 50% Field Verification", "T0 + 180 Days", 25, 55),
        ("M-4", "100% Survey Completion, UPIN Geo-tagging & Database Validation", "T0 + 270 Days", 25, 80),
        ("M-5", "Web GIS Portal Deployment, User Acceptance Testing (UAT) & Training", "T0 + 330 Days", 10, 90),
        ("M-6", "Final Handover Sign-off & Commencement of AMC / Operations", "T0 + 365 Days", 10, 100)
    ]
    
    for idx, (m_c, m_d, m_t, m_p, m_cum) in enumerate(m_rows, start=4):
        ws2.append([m_c, m_d, m_t, m_p, m_cum])
        for col_i in range(1, 6):
            c_cell = ws2.cell(row=idx, column=col_i)
            c_cell.font = body_font
            c_cell.border = thin_border
            if col_i in [4, 5]:
                c_cell.alignment = Alignment(horizontal="right")
                c_cell.number_format = "0\"%\""
            else:
                c_cell.alignment = Alignment(horizontal="left" if col_i == 2 else "center")
                
    ws2.column_dimensions['A'].width = 14
    ws2.column_dimensions['B'].width = 65
    ws2.column_dimensions['C'].width = 18
    ws2.column_dimensions['D'].width = 20
    ws2.column_dimensions['E'].width = 20
    
    # SHEET 3: Bidder Undertaking
    ws3 = wb.create_sheet(title="Bidder Declaration")
    ws3["A1"] = "STATUTORY UNDERTAKING BY COMMERCIAL BIDDER"
    ws3["A1"].font = title_font
    
    declaration_text = [
        "",
        "1. We confirm that the rates quoted above in the Item Rate BoQ are complete and inclusive of all taxes,",
        "   duties, levies, transportation, insurance, survey sensor equipment, software licenses, and field manpower.",
        "2. The financial proposal shall remain valid for 180 calendar days from the date of technical bid opening.",
        "3. We understand that mathematical formulas in the official Excel BOQ are automated and verify all calculations.",
        "4. In case of any mathematical discrepancy between unit rates and total amount, unit rates shall prevail.",
        "",
        "Name of Authorized Signatory: ________________________________________________",
        "Designation: _______________________________________________________________",
        "Company Seal & Digital Signature: ___________________________________________"
    ]
    for line in declaration_text:
        ws3.append([line])
        
    wb.save(str(target_path))
    return target_path


def make_authentic_docx(target_path, tender, state_name, kw_name, file_name=""):
    """
    Generate an authentic, multi-section official Government Word Document (.docx / .doc)
    complete with official heading, domain specifications, technical requirements,
    eligibility criteria, and legal conditions.
    """
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tender_id = getattr(tender, "tender_id", "REF-2026")
    title = getattr(tender, "title", str(tender))
    dept = getattr(tender, "department", "GOVERNMENT DIRECTORATE")
    desc = getattr(tender, "description", "")
    pub_date = getattr(tender, "published_date", None) or datetime.utcnow()
    last_date = getattr(tender, "last_date", None) or (datetime.utcnow() + timedelta(days=21))

    profile = get_domain_profile(title, kw_name, dept, desc)

    doc = docx.Document()

    # Document Header
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_emblem = p_header.add_run("GOVERNMENT OF " + str(state_name).upper() + "\n")
    r_emblem.bold = True
    r_emblem.font.size = Pt(14)
    r_emblem.font.color.rgb = RGBColor(16, 44, 87)

    r_dept = p_header.add_run(str(dept).upper() + "\n")
    r_dept.bold = True
    r_dept.font.size = Pt(12)
    r_dept.font.color.rgb = RGBColor(30, 41, 59)

    r_portal = p_header.add_run("STATE e-PROCUREMENT TENDER DOCUMENTATION\n")
    r_portal.font.size = Pt(10)
    r_portal.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph("―" * 45).alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run(f"VOLUME I: REQUEST FOR PROPOSAL (RFP) &\nTECHNICAL SPECIFICATION SCHEDULE\n\nRef No: {tender_id}\n")
    r_title.bold = True
    r_title.font.size = Pt(13)
    r_title.font.color.rgb = RGBColor(15, 23, 42)

    # Key Tender Information Table
    table = doc.add_table(rows=6, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    info_data = [
        ("Tender Notice / IFB Reference", str(tender_id)),
        ("Name of Work / Project Title", str(title)),
        ("Procuring Department / Authority", str(dept)),
        ("Domain Classification & Keyword", f"{profile['domain_title']} ({kw_name})"),
        ("Bid Publication Date & Time", pub_date.strftime("%d/%m/%Y %I:%M %p")),
        ("Bid Submission Closing Deadline", last_date.strftime("%d/%m/%Y %I:%M %p"))
    ]

    for i, (k, v) in enumerate(info_data):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.text = k
        c0.paragraphs[0].runs[0].bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c1.text = v
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)

    doc.add_paragraph("")

    # Section 1: Introduction & Background
    doc.add_heading("1. INTRODUCTION AND PROJECT SCOPE", level=1)
    p_scope = doc.add_paragraph(profile["scope_desc"])
    p_scope.paragraph_format.line_spacing = 1.15

    # Section 2: Technical Specifications & Geodetic Standards
    doc.add_heading("2. TECHNICAL SPECIFICATIONS & STANDARDS", level=1)
    tech_paras = [
        "2.1 Geodetic Datum & Spatial Reference: All spatial mapping, drone photogrammetry, and LiDAR surveys must be referenced to WGS84 Datum with Universal Transverse Mercator (UTM) Projection. Ground control network must link directly to Survey of India (SoI) CORS stations with baseline verification < 5 mm.",
        "2.2 Absolute Accuracy & Resolution: Horizontal absolute root mean square error (RMSE) must not exceed 5.0 cm on hard surfaces, and vertical RMSE < 10.0 cm. Orthomosaic imagery must be generated at Ground Sampling Distance (GSD) of 5 cm or better, delivered in GeoTIFF / ECW formats with OGC-compliant metadata.",
        "2.3 Enterprise Web-GIS Software Architecture: The central spatial database must be deployed on open enterprise stack (PostgreSQL with PostGIS spatial extensions, GeoServer, and React / Leaflet frontends). All spatial layers must expose standard OGC services (WMS, WFS, WCS) with JWT role-based access control.",
        "2.4 Data Security & Compliance: In compliance with National Geospatial Policy (NGP 2022) and MeitY Guidelines, all spatial data, LiDAR clouds, and raster rasters must be stored on MeitY-empanelled Tier-III cloud data centers located physically within the Union of India."
    ]
    for tp in tech_paras:
        doc.add_paragraph(tp)

    # Section 3: Detailed BOQ Items Table
    doc.add_heading("3. BILL OF QUANTITIES (BOQ) & PRICING SCHEDULE", level=1)
    boq_table = doc.add_table(rows=len(profile["boq_items"]) + 1, cols=6)
    boq_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    boq_table.style = 'Table Grid'

    headers = ["Item", "Description of Work", "Qty", "Unit", "Rate (INR)", "Total (INR)"]
    hdr_row = boq_table.rows[0]
    for j, h in enumerate(headers):
        hdr_row.cells[j].text = h
        hdr_row.cells[j].paragraphs[0].runs[0].bold = True
        hdr_row.cells[j].paragraphs[0].runs[0].font.size = Pt(9)

    total_est = 0
    for idx, item in enumerate(profile["boq_items"]):
        row = boq_table.rows[idx + 1]
        item_no, item_desc, qty, unit, rate = item
        item_tot = qty * rate
        total_est += item_tot

        row.cells[0].text = str(item_no)
        row.cells[1].text = str(item_desc)
        row.cells[2].text = f"{qty:,}"
        row.cells[3].text = str(unit)
        row.cells[4].text = f"{rate:,.2f}"
        row.cells[5].text = f"{item_tot:,.2f}"
        for cell in row.cells:
            cell.paragraphs[0].runs[0].font.size = Pt(8.5)

    doc.add_paragraph(f"\nEstimated Contract Value (ECV): INR {total_est:,.2f} + GST 18.00% applicable as per Government of India taxation rules.")

    # Section 4: Eligibility Criteria
    doc.add_heading("4. MINIMUM BIDDER ELIGIBILITY CRITERIA", level=1)
    crit_paras = [
        f"4.1 Financial Turnover: The bidder must have an average annual financial turnover of at least INR {profile['turnover_cr']} Crores over the preceding three financial years (certified by a practicing Chartered Accountant with valid UDIN).",
        f"4.2 Past Experience: {profile['past_exp']}",
        f"4.3 Key Technical Expert: {profile['lead_expert']}",
        "4.4 Quality & Information Security Certifications: The lead bidder must hold valid ISO 9001:2015 (Quality Management), ISO 27001:2022 (Information Security Management), and CMMI Level 3 or higher certification on the date of bid submission."
    ]
    for cp in crit_paras:
        doc.add_paragraph(cp)

    # Section 5: Legal & Submission Terms
    doc.add_heading("5. GENERAL TENDER CONDITIONS & SUBMISSION", level=1)
    cond_paras = [
        "5.1 Online Submission Only: Bids must be submitted strictly in electronic format through the official state e-procurement portal. Hardcopy submissions shall not be accepted for price bids.",
        "5.2 Earnest Money Deposit (EMD): EMD must be remitted electronically via the online payment gateway or Bank Guarantee as specified in the e-procurement platform.",
        "5.3 Bid Validity: All submitted proposals and rates shall remain valid for a period of 120 (One Hundred and Twenty) calendar days from the opening date of the technical bid.",
        "5.4 Consortium / Joint Venture: Consortium or Joint Venture bidding is permissible with maximum two partners, where the Lead Bidder must hold at least 51% equity participation."
    ]
    for cnd in cond_paras:
        doc.add_paragraph(cnd)

    # Sign-off Block
    doc.add_paragraph("\n\n" + "_" * 40)
    p_sign = doc.add_paragraph()
    p_sign.add_run(f"For and on behalf of Government of {state_name}\n").bold = True
    p_sign.add_run(f"Authorized Signatory & Competent Tender Inviting Authority\n{dept}\n")
    p_sign.add_run("[OFFICIAL DIGITAL SIGNATURE VERIFIED]")

    doc.save(str(target_path))
    return target_path


def make_bundle_zip(target_path, tender, state_name, kw_name):
    """
    Generate a complete ZIP archive bundling all authentic tender documents
    (Notice, Technical Specs, Excel BOQ, and Conditions).
    """
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    tender_id = getattr(tender, "tender_id", "REF-2026")
    title = getattr(tender, "title", str(tender))
    dept = getattr(tender, "department", "Dept")
    
    pdf_notice = target_path.parent / f"Tendernotice_{tender_id}.pdf"
    if not pdf_notice.exists():
        make_authentic_pdf(pdf_notice, tender, state_name, kw_name, pdf_notice.name)
        
    boq_xlsx = target_path.parent / f"BOQ_Financial_Schedule_{tender_id}.xlsx"
    if not boq_xlsx.exists():
        make_simple_xlsx(boq_xlsx, title, str(tender_id), dept, kw_name)
        
    added_names = set()
    with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if pdf_notice.exists() and pdf_notice.name not in added_names:
            zf.write(pdf_notice, arcname=pdf_notice.name)
            added_names.add(pdf_notice.name)
        if boq_xlsx.exists() and boq_xlsx.name not in added_names:
            zf.write(boq_xlsx, arcname=boq_xlsx.name)
            added_names.add(boq_xlsx.name)
        for f in target_path.parent.iterdir():
            if f.is_file() and f != target_path and f.suffix.lower() in [".pdf", ".xlsx", ".xls", ".doc", ".docx"]:
                if f.name not in added_names:
                    zf.write(f, arcname=f.name)
                    added_names.add(f.name)
                
    return target_path
