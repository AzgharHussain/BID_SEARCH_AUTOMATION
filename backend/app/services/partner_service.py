import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import models
from app.schemas import schemas

# Comprehensive initial seed dataset representing prominent Indian geospatial, survey, IT, and infra firms
INITIAL_PARTNERS_SEED = [
    {
        "name": "AeroSky Dynamics Technologies Pvt Ltd",
        "short_name": "AeroSky Dynamics",
        "primary_domain": "Drone LiDAR & Aerial Mapping",
        "secondary_domains": json.dumps(["UAV Photogrammetry", "Aerial LiDAR", "DGPS Cadastral Survey", "Corridor Mapping"]),
        "description": "Leading Indian aerial surveying and drone technology enterprise. Operates DGCA Type-Certified high-end LiDAR drones, multispectral sensors, and heavy-payload mapping UAVs with 40+ certified remote pilots across India.",
        "certifications": json.dumps(["DGCA Type Certified (Small & Medium UAVs)", "ISO 9001:2015", "ISO 27001", "Survey of India Empaneled", "GeM Star Registered"]),
        "empanelment_status": "DGCA Certified UAV Operator & Survey of India Empaneled",
        "turnover": "₹38.5 Cr (FY 2024-25)",
        "employee_count": "110+ Technical Staff & 42 Certified Pilots",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Vikram Malhotra",
        "designation": "Vice President - Strategic Alliances & JV Bids",
        "email": "partnerships@aerosky.in",
        "phone": "+91 98490 12845",
        "website": "https://www.aeroskydynamics.in",
        "past_projects": json.dumps([
            {"title": "SVAMITVA Scheme Drone Cadastral Mapping of 1,200 Villages", "client": "Survey of India / Govt of Maharashtra", "value": "₹14.2 Cr"},
            {"title": "High-Speed Rail Corridor 3D LiDAR Topographic Survey", "client": "NHSRCL / Gujarat PWD", "value": "₹8.6 Cr"},
            {"title": "Mining Lease Volume Estimation & Drone Monitoring", "client": "Odisha Mining Corporation", "value": "₹5.4 Cr"}
        ]),
        "synergy_roles": json.dumps(["Drone Flight Operations Lead", "Sensor & LiDAR Hardware Provider", "Raw Point-Cloud Pre-processing"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "OrbitGeo Space Solutions India",
        "short_name": "OrbitGeo",
        "primary_domain": "Satellite Imagery & Remote Sensing Analytics",
        "secondary_domains": json.dumps(["Earth Observation Data", "Radar Interferometry (InSAR)", "Crop Health Analytics", "Change Detection"]),
        "description": "Premier satellite data aggregator and space-tech analytics firm. Direct commercial distribution partner for Maxar WorldView (30cm), PlanetScope, Sentinel, and ISRO Cartosat constellations with automated cloud-based processing pipelines.",
        "certifications": json.dumps(["ISRO/NRSC Authorized Partner", "ISO 9001:2015", "CMMI Level 3", "Space-Tech India Certified"]),
        "empanelment_status": "ISRO / NRSC Commercial Imagery Distributor",
        "turnover": "₹46.2 Cr (FY 2024-25)",
        "employee_count": "85 Remote Sensing Specialists & Data Scientists",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Dr. Shalini Raman",
        "designation": "Head of Earth Observation & Govt Alliances",
        "email": "shalini.raman@orbitgeo.in",
        "phone": "+91 80 4125 7890",
        "website": "https://www.orbitgeospace.in",
        "past_projects": json.dumps([
            {"title": "Statewide High-Resolution Satellite Base Map & Land Use Classification", "client": "Andhra Pradesh Space Applications Centre (APSAC)", "value": "₹12.0 Cr"},
            {"title": "Satellite InSAR Land Subsidence & Infrastructure Monitoring", "client": "Delhi Metro Rail Corporation (DMRC)", "value": "₹6.8 Cr"},
            {"title": "Satellite-based Crop Health & Yield Assessment", "client": "Maharashtra Agriculture Department", "value": "₹9.5 Cr"}
        ]),
        "synergy_roles": json.dumps(["Satellite Data Sourcing Partner", "High-Resolution Stereo Orthorectification", "Spectral AI Feature Extraction"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "IndoCloud MeitY Data Services Ltd",
        "short_name": "IndoCloud",
        "primary_domain": "MeitY-Empaneled Cloud & Data Center Infrastructure",
        "secondary_domains": json.dumps(["GovCloud Tier-3/Tier-4 Hosting", "STQC Cyber Security Auditing", "Disaster Recovery", "Spatial Database Hosting"]),
        "description": "MeitY-empaneled Indian sovereign cloud service provider. Operates Tier-3 and Tier-4 data centers across Mumbai, Delhi NCR, and Chennai, fully compliant with NIC/Govt cloud security guidelines, STQC audit standards, and data residency laws.",
        "certifications": json.dumps(["MeitY Empaneled Cloud Provider", "ISO 27001", "ISO 20000-1", "ISO 22301", "SOC 2 Type II", "Cert-In Empaneled"]),
        "empanelment_status": "MeitY Empaneled Cloud Service Provider (GovCloud)",
        "turnover": "₹125.0 Cr (FY 2024-25)",
        "employee_count": "280+ Cloud Engineers & Security Analysts",
        "state": "Delhi",
        "city": "New Delhi",
        "pan_india_presence": True,
        "contact_person": "Rajeshwari Iyer",
        "designation": "Director - Public Sector Cloud & GovTech",
        "email": "gov.alliances@indocloud.in",
        "phone": "+91 11 4980 3320",
        "website": "https://www.indocloud.in",
        "past_projects": json.dumps([
            {"title": "State Spatial Data Infrastructure (SSDI) High-Availability Cloud Hosting", "client": "Karnataka State Remote Sensing Applications Centre", "value": "₹18.5 Cr"},
            {"title": "Integrated Command and Control Center (ICCC) Cloud Infrastructure", "client": "Smart City Mission - UP Govt", "value": "₹24.0 Cr"},
            {"title": "E-Governance Spatial Registry Database Cluster", "client": "Rajasthan IT Department", "value": "₹11.2 Cr"}
        ]),
        "synergy_roles": json.dumps(["MeitY Cloud Infrastructure Lead", "STQC Security & NIC Compliance Lead", "Spatial Database High-Availability Host"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "TerraSurvey & Cadastral Geospatial Tech",
        "short_name": "TerraSurvey",
        "primary_domain": "DGPS & Cadastral Ground Survey",
        "secondary_domains": json.dumps(["Total Station Ground Survey", "ETS Topographic Profiling", "Boundary Demarcation", "Land Revenue Mapping"]),
        "description": "Pioneering Indian land surveying organization with 50+ dual-frequency GNSS/DGPS rover units and 30 electronic total stations. Extensive field presence in rural and urban cadastral demarcation and revenue land resurvey.",
        "certifications": json.dumps(["Survey of India Class-A Empaneled", "ISO 9001:2015", "NABL Calibration Accredited", "State Land Records Approved"]),
        "empanelment_status": "Survey of India Class-A Empaneled Land Surveyor",
        "turnover": "₹22.8 Cr (FY 2024-25)",
        "employee_count": "150+ Ground Surveyors, Cartographers & Revenue Experts",
        "state": "Maharashtra",
        "city": "Pune",
        "pan_india_presence": True,
        "contact_person": "Er. Nilesh Kulkarni",
        "designation": "Managing Partner - Cadastral Field Operations",
        "email": "nilesh@terrasurvey.in",
        "phone": "+91 94220 54129",
        "website": "https://www.terrasurvey.in",
        "past_projects": json.dumps([
            {"title": "Agricultural Cadastral Resurvey of 450 Revenue Villages", "client": "Maharashtra Land Records Department", "value": "₹11.5 Cr"},
            {"title": "DGPS Control Network and Ground Control Points (GCPs) for Aerial Survey", "client": "National Highways Authority of India (NHAI)", "value": "₹5.8 Cr"},
            {"title": "Riverbed Topographic Cross-Section Survey", "client": "Water Resources Dept, Govt of Karnataka", "value": "₹4.2 Cr"}
        ]),
        "synergy_roles": json.dumps(["Field Ground-Truthing Operations Lead", "DGPS GCP Network Establishment", "Cadastral Boundary Validation"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "GeoVision AI & Deep Learning Labs",
        "short_name": "GeoVision AI",
        "primary_domain": "AI / Computer Vision & Geospatial Analytics",
        "secondary_domains": json.dumps(["Automated Feature Extraction", "Building Footprint AI", "Road Network Extraction", "Agricultural AI Analytics"]),
        "description": "Deep-tech geospatial AI lab specializing in computer vision models trained specifically on Indian terrain and built environments. Automated extraction of 2D/3D building footprints, rooftop solar suitability, and encroachment analytics.",
        "certifications": json.dumps(["NASSCOM AI Center of Excellence Member", "ISO 27001", "CMMI Level 3", "MeitY Start-Up India Certified"]),
        "empanelment_status": "NASSCOM CoE Partner & Digital India Contributor",
        "turnover": "₹18.4 Cr (FY 2024-25)",
        "employee_count": "60 AI/ML Researchers, Geospatial Developers & Engineers",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Ananya Deshmukh",
        "designation": "Chief Technology Alliances Officer",
        "email": "partnerships@geovisionai.io",
        "phone": "+91 80 6712 9000",
        "website": "https://www.geovisionai.io",
        "past_projects": json.dumps([
            {"title": "AI Automated Building Footprint & Rooftop Extraction from 10cm Drone Orthomosaics", "client": "Delhi Urban Development Authority", "value": "₹7.4 Cr"},
            {"title": "Deep Learning Waterbody Encroachment & Wetland Shrinkage Monitoring", "client": "Tamil Nadu PWD & Water Resources", "value": "₹5.1 Cr"},
            {"title": "Satellite-based Crop Classification & Damage Assessment AI", "client": "Punjab Remote Sensing Centre (PRSC)", "value": "₹6.3 Cr"}
        ]),
        "synergy_roles": json.dumps(["AI Model Inference Lead", "Automated Vector Extraction", "High-Throughput Feature Recognition Pipeline"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "HydraTech Water & SCADA Systems Pvt Ltd",
        "short_name": "HydraTech Water",
        "primary_domain": "Water Resources, SCADA & IoT Telemetry",
        "secondary_domains": json.dumps(["Canal Automation SCADA", "River Basin Flood Modeling", "Groundwater Telemetry", "IoT Water Metering"]),
        "description": "Specialized water infrastructure informatics company. Designs and deploys ultrasonic flow sensors, acoustic Doppler velocity meters, automatic sluice gate controllers, and integrates hydraulic modeling (HEC-RAS/MIKE) with GIS dashboards.",
        "certifications": json.dumps(["Central Water Commission (CWC) Empaneled", "ISO 9001:2015", "CE Certified Sensors", "Jal Jeevan Mission Partner"]),
        "empanelment_status": "Central Water Commission (CWC) Empaneled Vendor",
        "turnover": "₹34.0 Cr (FY 2024-25)",
        "employee_count": "95 Hydrologists, Instrumentation Engineers & SCADA Specialists",
        "state": "Gujarat",
        "city": "Ahmedabad",
        "pan_india_presence": True,
        "contact_person": "Pradeep Patel",
        "designation": "Vice President - Water Infrastructure Solutions",
        "email": "p.patel@hydratechwater.com",
        "phone": "+91 79 2658 4410",
        "website": "https://www.hydratechwater.com",
        "past_projects": json.dumps([
            {"title": "Canal Automation & Real-time Flow Telemetry for 250km Branch Network", "client": "Sardar Sarovar Narmada Nigam Ltd", "value": "₹16.5 Cr"},
            {"title": "Flood Early Warning Decision Support System (FEWDSS)", "client": "Krishna River Basin, Andhra Pradesh WRD", "value": "₹12.2 Cr"},
            {"title": "Groundwater Table Monitoring with 500 Piezometric Telemetry Stations", "client": "Central Ground Water Board (CGWB)", "value": "₹8.9 Cr"}
        ]),
        "synergy_roles": json.dumps(["Water Telemetry & Sensor Deployment", "Hydraulic Modeling (HEC-RAS)", "Real-time SCADA System Integration"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "UrbanInfra Geospatial & Smart City Planners",
        "short_name": "UrbanInfra",
        "primary_domain": "Smart Cities, Municipal GIS & Urban Infrastructure",
        "secondary_domains": json.dumps(["3D City Digital Twins", "Property Tax GIS Survey", "Underground Utility GIS", "Town Planning Master Plans"]),
        "description": "Consulting and geospatial engineering practice for urban local bodies and municipal corporations. Has mapped over 2.5 million municipal properties for GIS-based property tax collection and built 3D BIM-GIS city models.",
        "certifications": json.dumps(["Ministry of Housing & Urban Affairs (MoHUA) Empaneled", "Institute of Town Planners India (ITPI)", "ISO 9001", "CMMI Level 3"]),
        "empanelment_status": "MoHUA Empaneled Urban Development Consultant",
        "turnover": "₹29.5 Cr (FY 2024-25)",
        "employee_count": "80 Urban Planners, Municipal Surveyors & GIS Analysts",
        "state": "Maharashtra",
        "city": "Mumbai",
        "pan_india_presence": True,
        "contact_person": "Ar. Sanjay Mehta",
        "designation": "Principal Partner - Smart City Consultancies",
        "email": "smehta@urbaninfra.co.in",
        "phone": "+91 22 2845 1190",
        "website": "https://www.urbaninfra.co.in",
        "past_projects": json.dumps([
            {"title": "3D Digital Twin City Model & Web Portal for Pune Smart City", "client": "Pune Smart City Development Corp (PSCDCL)", "value": "₹13.8 Cr"},
            {"title": "GIS-based Property Tax Assessment & Door-to-Door DGPS Survey of 400,000 Properties", "client": "Surat Municipal Corporation", "value": "₹9.2 Cr"},
            {"title": "Subsurface GPR & Utility Mapping for Metro Rail Corridor", "client": "Mumbai Metropolitan Region Development Authority (MMRDA)", "value": "₹7.1 Cr"}
        ]),
        "synergy_roles": json.dumps(["Municipal GIS Domain Lead", "Property Tax Survey & Reconciliation", "3D City Model & BIM Integration"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "MapCore Enterprise Geoportals Pvt Ltd",
        "short_name": "MapCore",
        "primary_domain": "GIS & Spatial Web Application Development",
        "secondary_domains": json.dumps(["Open Source WebGIS (GeoServer/PostGIS)", "Esri ArcGIS Enterprise Implementation", "Mobile Survey Apps (Offline Sync)", "Spatial Big Data Analytics"]),
        "description": "Enterprise software engineering firm focusing on state-scale Geoportals, SDI nodes, and custom spatial decision support systems. Team consists of full-stack GIS developers, PostGIS database administrators, and cloud architects.",
        "certifications": json.dumps(["CMMI Level 5 (Development)", "ISO 9001:2015", "ISO 27001", "Cert-In Safe-to-Host Security Audited", "State IT Dept Empaneled"]),
        "empanelment_status": "State Electronics Development Corp Empaneled IT Vendor",
        "turnover": "₹52.0 Cr (FY 2024-25)",
        "employee_count": "140 Software Engineers & GIS Solution Architects",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "pan_india_presence": True,
        "contact_person": "K. Sundaram",
        "designation": "Director - Government Enterprise Solutions",
        "email": "ksundaram@mapcore.in",
        "phone": "+91 44 4210 8870",
        "website": "https://www.mapcore.in",
        "past_projects": json.dumps([
            {"title": "Statewide Spatial Data Infrastructure & WebGIS Geoportal (TNGIS)", "client": "Tamil Nadu e-Governance Agency (TNeGA)", "value": "₹17.4 Cr"},
            {"title": "Comprehensive Land Information Management System (LIMS) Portal", "client": "Kerala Revenue & Registration Dept", "value": "₹11.8 Cr"},
            {"title": "Spatial MIS for Rural Road Network (PMGSY)", "client": "Ministry of Rural Development", "value": "₹8.5 Cr"}
        ]),
        "synergy_roles": json.dumps(["WebGIS Geoportal Development Lead", "PostGIS Spatial Database Architect", "Cert-In Security Cleared Front/Backend Engine"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "GreenEco Forest & Environmental Informatics",
        "short_name": "GreenEco Tech",
        "primary_domain": "Forest, Environmental & Carbon Assessment",
        "secondary_domains": json.dumps(["Forest Canopy Density Mapping", "EIA & Environmental Auditing", "Wildlife Corridor Telemetry", "Carbon Sequestration GIS"]),
        "description": "Premier environmental remote sensing and forest geospatial consultancy. Specializes in vegetation indices, biomass calculation, LiDAR tree canopy profiling, wildlife habitat suitability modeling, and environmental clearance GIS.",
        "certifications": json.dumps(["MoEFCC Empaneled Environmental Consultant", "QCI/NABET Accredited EIA Consultant", "ISO 14001:2015", "Forest Survey of India Research Partner"]),
        "empanelment_status": "MoEFCC / QCI NABET Empaneled EIA & Forestry Partner",
        "turnover": "₹16.7 Cr (FY 2024-25)",
        "employee_count": "55 Ecologists, Remote Sensing Scientists & Forest Officers",
        "state": "Uttarakhand",
        "city": "Dehradun",
        "pan_india_presence": True,
        "contact_person": "Dr. R. K. Bhattacharya",
        "designation": "Director - Ecological Remote Sensing & Forestry",
        "email": "rk.bhatt@greenecotech.org",
        "phone": "+91 135 274 5510",
        "website": "https://www.greenecotech.org",
        "past_projects": json.dumps([
            {"title": "Statewide Forest Canopy Density & Carbon Stock Mapping using Sentinel-2 and Airborne LiDAR", "client": "Madhya Pradesh Forest Department", "value": "₹8.9 Cr"},
            {"title": "Wildlife Corridor GIS Mapping & Human-Elephant Conflict Early Warning", "client": "Assam & West Bengal Forest Directorate", "value": "₹6.2 Cr"},
            {"title": "Catchment Area Treatment (CAT) Plan GIS Studies", "client": "Tehri Hydro Development Corporation (THDC)", "value": "₹4.8 Cr"}
        ]),
        "synergy_roles": json.dumps(["Forest Canopy & Ecological Modeling", "NABET Accredited Environmental Clearance", "Biodiversity Corridor Habitat Analysis"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Apex Infra-Tech & Corridors India",
        "short_name": "Apex Infra-Tech",
        "primary_domain": "Civil & Infrastructure Engineering Surveys",
        "secondary_domains": json.dumps(["Highway DPR Surveys", "Railway Track Alignment", "Geotechnical Borehole Investigation", "Utility Shifting Mapping"]),
        "description": "Heavy infrastructure engineering and highway survey enterprise. Equipped with mobile mapping laser scanners, subsurface utility radars, geotechnical drilling rigs, and bridge inspection equipment.",
        "certifications": json.dumps(["NHAI Empaneled Technical Consultant", "Indian Railways RDSO Approved", "ISO 9001:2015", "NABL Material Testing Lab"]),
        "empanelment_status": "NHAI & RDSO Approved Engineering Survey Consultant",
        "turnover": "₹68.0 Cr (FY 2024-25)",
        "employee_count": "175 Civil Engineers, Geologists & Survey Crew",
        "state": "West Bengal",
        "city": "Kolkata",
        "pan_india_presence": True,
        "contact_person": "Bimal Ghosh",
        "designation": "General Manager - Tenders & Consortiums",
        "email": "bimal.ghosh@apexinfra.co.in",
        "phone": "+91 33 2419 6600",
        "website": "https://www.apexinfra.co.in",
        "past_projects": json.dumps([
            {"title": "Topographic Alignment & DPR Survey for 180km Greenfield Expressway", "client": "National Highways Authority of India (NHAI)", "value": "₹19.4 Cr"},
            {"title": "Subsurface Utility Detection & Ground Penetrating Radar (GPR) Survey", "client": "Kolkata Metro Rail Corporation (KMRC)", "value": "₹8.7 Cr"},
            {"title": "Dedicated Freight Corridor Track Geometric Profiling", "client": "DFCCIL / Ministry of Railways", "value": "₹14.0 Cr"}
        ]),
        "synergy_roles": json.dumps(["Civil DPR & Engineering Survey Lead", "Geotechnical & Subsurface GPR Investigation", "NHAI/RDSO Technical Compliance"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Quantum LiDAR & Sensor Systems",
        "short_name": "Quantum Sensors",
        "primary_domain": "LiDAR Equipment OEM & Sensor Calibration",
        "secondary_domains": json.dumps(["Mobile LiDAR Systems", "Airborne Sensor Leasing", "Hydrographic Bathymetric Echo Sounders", "NABL Sensor Calibration"]),
        "description": "High-accuracy sensor manufacturing, leasing, and calibration firm. Provides state-of-the-art dual-return airborne LiDAR pods, mobile laser mapping vehicles, and single/multibeam bathymetric echo sounders with full operational support.",
        "certifications": json.dumps(["GeM Star OEM Seller", "CE & FCC Certified", "ISO 9001:2015", "NABL Calibration Lab"]),
        "empanelment_status": "GeM Registered High-Precision Sensor OEM",
        "turnover": "₹41.0 Cr (FY 2024-25)",
        "employee_count": "70 Sensor Hardware Specialists & Optics Engineers",
        "state": "Haryana",
        "city": "Gurugram",
        "pan_india_presence": True,
        "contact_person": "Harish Chawla",
        "designation": "Head of Sales & Government Empanelments",
        "email": "hchawla@quantumsensors.in",
        "phone": "+91 124 456 7810",
        "website": "https://www.quantumsensors.in",
        "past_projects": json.dumps([
            {"title": "Supply and Field Deployment of 6 Mobile LiDAR Vehicle Rigs for City Mapping", "client": "Jaipur Development Authority (JDA)", "value": "₹12.5 Cr"},
            {"title": "Airborne Topo-Bathymetric LiDAR Sensor Lease for Coastal Inundation Studies", "client": "National Centre for Coastal Research (NCCR)", "value": "₹9.8 Cr"},
            {"title": "Annual Maintenance & NABL Calibration Contract for 80 DGPS Receivers", "client": "Survey of India Northern Zone", "value": "₹3.6 Cr"}
        ]),
        "synergy_roles": json.dumps(["Specialized Sensor & LiDAR Hardware Lease", "NABL Instrument Calibration Certification", "On-Field Hardware Maintenance & Hot-Swap Spares"]),
        "rating": 4.7,
        "status": "Available"
    },
    {
        "name": "Zenith Geo-Intelligence Consortium India",
        "short_name": "Zenith Geo-Intel",
        "primary_domain": "Turnkey Geospatial Bidding & Consortium Lead",
        "secondary_domains": json.dumps(["Turnkey Project Management", "Financial Consortium Lead", "Bank Guarantee & Bonding", "Large-scale Field Deployment"]),
        "description": "Tier-1 national systems integrator and government tender partner with ₹88+ Cr annual turnover. Frequently acts as Lead Consortium Partner for bids with strict financial turnover thresholds (₹50-100 Cr) while GISFY executes technical geospatial scope.",
        "certifications": json.dumps(["NICSI Empaneled System Integrator", "CMMI Level 5", "ISO 9001", "ISO 27001", "ISO 22301", "NSIC Certified"]),
        "empanelment_status": "NICSI Empaneled Tier-1 System Integrator",
        "turnover": "₹88.5 Cr (FY 2024-25)",
        "employee_count": "320+ Management, Technical & Field Personnel",
        "state": "Delhi",
        "city": "New Delhi",
        "pan_india_presence": True,
        "contact_person": "Col. Maninder Singh (Retd.)",
        "designation": "Managing Director - Public Sector Bids & Strategic Consortiums",
        "email": "maninder.singh@zenithgeointel.com",
        "phone": "+91 11 4150 9988",
        "website": "https://www.zenithgeointel.com",
        "past_projects": json.dumps([
            {"title": "Turnkey Enterprise GIS & Spatial Data Repository for 12 Smart Cities", "client": "Ministry of Housing & Urban Affairs", "value": "₹36.0 Cr"},
            {"title": "National Land Records Modernization Programme (NLRMP) Implementation", "client": "Department of Land Resources (DoLR)", "value": "₹28.5 Cr"},
            {"title": "Statewide Drone Survey & Land Records Computerization", "client": "Revenue Department, Govt of Haryana", "value": "₹19.2 Cr"}
        ]),
        "synergy_roles": json.dumps(["Financial Criteria & Consortium Lead Bidder", "Earnest Money Deposit (EMD) & Performance BG Facilitator", "End-to-End Turnkey Delivery Governance"]),
        "rating": 4.9,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # ANDHRA PRADESH LOCAL VENDORS
    # -------------------------------------------------------------
    {
        "name": "Amaravati Drone & Geospatial Solutions Pvt Ltd",
        "short_name": "Amaravati Drones",
        "primary_domain": "Drone LiDAR & Aerial Mapping",
        "secondary_domains": json.dumps(["UAV Photogrammetry", "SVAMITVA Village Mapping", "Canal Cross-Section Survey", "Corridor LiDAR"]),
        "description": "Specialized Andhra Pradesh aerial survey and UAV photogrammetry firm based in Vijayawada. Key empanelled contractor for A.P. Drones Corporation and APSAC, having surveyed over 800 gram panchayats under SVAMITVA / YSR Jagananna Saswatha Bhoo Hakku schemes.",
        "certifications": json.dumps(["DGCA Type Certified UAV Fleet", "APSAC Empaneled Class-A Drone Operator", "ISO 9001:2015", "GeM Star Seller"]),
        "empanelment_status": "A.P. Drones Corporation & APSAC Empaneled Class-A Drone Operator",
        "turnover": "₹24.5 Cr (FY 2024-25)",
        "employee_count": "65 Drone Pilots, Photogrammetry Specialists & Cadastral Surveyors",
        "state": "Andhra Pradesh",
        "city": "Vijayawada",
        "pan_india_presence": True,
        "contact_person": "K. Venkat Ramana",
        "designation": "Executive Director - Govt UAV Operations",
        "email": "alliances@amaravatidrones.in",
        "phone": "+91 866 249 7800",
        "website": "https://www.amaravatidrones.in",
        "past_projects": json.dumps([
            {"title": "SVAMITVA Scheme Drone Cadastral Mapping in 800 Villages", "client": "AP Drones Corp / Survey of India", "value": "₹9.8 Cr"},
            {"title": "Polavaram Left & Right Main Canal Topographic LiDAR", "client": "Water Resources Dept, Govt of AP", "value": "₹6.4 Cr"},
            {"title": "Amaravati Capital City Infrastructure 3D Mesh Mapping", "client": "APCRDA", "value": "₹4.7 Cr"}
        ]),
        "synergy_roles": json.dumps(["AP Ground Flight Crew & Drone Mobilization", "DGCA Type-Certified Fleet Deployment", "Local Revenue Boundary Cadastral Verification"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Vizag Coastal Geo-Informatics & Marine Tech",
        "short_name": "Vizag Marine Geo",
        "primary_domain": "Hydrographic Survey & Coastal GIS",
        "secondary_domains": json.dumps(["Bathymetric Echo Sounding", "Coastal Zone Management (CRZ)", "Port & Harbour Utility GIS", "Subsea Cable Survey"]),
        "description": "Premier maritime geospatial and bathymetric surveying company headquartered in Visakhapatnam. Operates dual-frequency multibeam sonar, side-scan sonars, and provides coastal vulnerability modeling for the entire Andhra coastline.",
        "certifications": json.dumps(["National Hydrographic Office (NHO) Certified Surveyors", "ISO 9001:2015", "ISO 14001", "MoEFCC CRZ Consultant"]),
        "empanelment_status": "Visakhapatnam Port Authority & AP Maritime Board Empaneled",
        "turnover": "₹21.0 Cr (FY 2024-25)",
        "employee_count": "45 Hydrographers, Marine Geologists & Ocean GIS Analysts",
        "state": "Andhra Pradesh",
        "city": "Visakhapatnam",
        "pan_india_presence": True,
        "contact_person": "Capt. Ramesh Varma (Retd.)",
        "designation": "Managing Director - Maritime & Coastal Tenders",
        "email": "ramesh.varma@vizagmarinegeo.com",
        "phone": "+91 891 278 4430",
        "website": "https://www.vizagmarinegeo.com",
        "past_projects": json.dumps([
            {"title": "Visakhapatnam Outer Harbour Multi-Beam Bathymetry & Siltation Study", "client": "Visakhapatnam Port Authority", "value": "₹7.2 Cr"},
            {"title": "AP Coastal Regulation Zone (CRZ) Cadastral High-Tide Line Demarcation", "client": "AP Coastal Zone Management Authority", "value": "₹5.5 Cr"},
            {"title": "Krishnapatnam Port Approach Channel Depth Validation", "client": "AP Maritime Board", "value": "₹3.8 Cr"}
        ]),
        "synergy_roles": json.dumps(["Marine & Coastal Bathymetric Survey Lead", "NHO Certified Sonar Data Processing", "Port Infrastructure GIS Integration"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Rayalaseema Geo-Survey & Water Telemetry",
        "short_name": "Rayalaseema Geo",
        "primary_domain": "Water Resources, SCADA & IoT Telemetry",
        "secondary_domains": json.dumps(["Groundwater Piezometer Telemetry", "Canal Flow SCADA", "Micro-Irrigation GIS", "DGPS Cadastral Survey"]),
        "description": "Specialized hydrological monitoring and telemetry enterprise with extensive presence across Rayalaseema districts (Chittoor, Kadapa, Anantapur, Kurnool). Deploys solar-powered telemetry flow meters and groundwater sensors.",
        "certifications": json.dumps(["Central Ground Water Board Empaneled", "ISO 9001:2015", "CE IoT Telemetry Sensors", "JJM AP Empaneled"]),
        "empanelment_status": "Andhra Pradesh Water Resources Department (APWRD) & CGWB Empaneled",
        "turnover": "₹17.8 Cr (FY 2024-25)",
        "employee_count": "50 Hydrologists, Instrumentation Technicians & DGPS Crew",
        "state": "Andhra Pradesh",
        "city": "Tirupati",
        "pan_india_presence": True,
        "contact_person": "S. Chandrasekhar Reddy",
        "designation": "Director - Water Grid Solutions",
        "email": "cs.reddy@rayalaseemageo.in",
        "phone": "+91 877 228 1900",
        "website": "https://www.rayalaseemageo.in",
        "past_projects": json.dumps([
            {"title": "Handri-Neeva Sujala Sravanthi Canal Telemetry & Flow Monitoring", "client": "Andhra Pradesh Water Resources Dept", "value": "₹8.4 Cr"},
            {"title": "Groundwater Table Automated Monitoring Network (400 Stations)", "client": "AP Ground Water Department", "value": "₹5.1 Cr"},
            {"title": "Tirupati Municipal Smart Water Distribution GIS", "client": "Tirupati Municipal Corporation", "value": "₹4.3 Cr"}
        ]),
        "synergy_roles": json.dumps(["Field IoT Telemetry Installation & Calibration", "AP Water Resources Department Protocol Compliance", "Local Rayalaseema District Survey Crew"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Andhra Geo-Cadastre & IT Solutions",
        "short_name": "Andhra Geo-Cadastre",
        "primary_domain": "DGPS & Cadastral Ground Survey",
        "secondary_domains": json.dumps(["ETS Boundary Demarcation", "Municipal GIS Property Survey", "Land Resurvey Database", "PostGIS Integration"]),
        "description": "Leading cadastral and land revenue survey firm in Andhra Pradesh. Equipped with 40+ Trimble dual-frequency GNSS receivers and an experienced team of retired state revenue survey officers.",
        "certifications": json.dumps(["Survey of India Empaneled", "ISO 9001:2015", "NIC-MeitY Compliant", "State Land Records Approved"]),
        "empanelment_status": "AP Survey and Land Records Department Class-A Empaneled",
        "turnover": "₹15.2 Cr (FY 2024-25)",
        "employee_count": "90 Ground Surveyors & Revenue GIS Draftsmen",
        "state": "Andhra Pradesh",
        "city": "Guntur",
        "pan_india_presence": True,
        "contact_person": "G. Harinath Babu",
        "designation": "Head of Cadastral Resurvey Operations",
        "email": "alliances@andhrageocadastre.com",
        "phone": "+91 863 234 6610",
        "website": "https://www.andhrageocadastre.com",
        "past_projects": json.dumps([
            {"title": "YSR Jagananna Bhoo Hakku Ground Resurvey of 300 Revenue Villages", "client": "AP Survey & Land Records Dept", "value": "₹7.9 Cr"},
            {"title": "Mangalagiri-Tadepalli Municipal Corporation DGPS Utility Survey", "client": "MTMC Urban Development", "value": "₹3.6 Cr"}
        ]),
        "synergy_roles": json.dumps(["Ground-Truthing & Revenue Field Demarcation", "State Land Record RoR Database Harmonization", "Local District Liaison & Revenue Approvals"]),
        "rating": 4.7,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # MAHARASHTRA LOCAL VENDORS
    # -------------------------------------------------------------
    {
        "name": "Mumbai SmartInfra Digital Twins Pvt Ltd",
        "short_name": "Mumbai SmartInfra",
        "primary_domain": "Smart Cities, Municipal GIS & Urban Infrastructure",
        "secondary_domains": json.dumps(["3D BIM-GIS Digital Twins", "Underground Utility GPR", "Property Tax Geo-Reconciliation", "Coastal Road LiDAR"]),
        "description": "Premier Mumbai metropolitan urban engineering firm specializing in 3D BIM-GIS integration, subsurface utility scanning (GPR), and high-density municipal GIS systems for BMC, MMRDA, and CIDCO.",
        "certifications": json.dumps(["BMC Empaneled Class-A IT & GIS Consultant", "ISO 27001", "CMMI Level 3", "MoHUA Urban Infrastructure Partner"]),
        "empanelment_status": "BMC (MCGM) & MMRDA Empaneled Urban Tech Consultant",
        "turnover": "₹36.0 Cr (FY 2024-25)",
        "employee_count": "85 3D Modelers, GIS Specialists & Civil Planners",
        "state": "Maharashtra",
        "city": "Mumbai",
        "pan_india_presence": True,
        "contact_person": "Aditya Dandekar",
        "designation": "VP - Municipal & Metro Rail Solutions",
        "email": "a.dandekar@mumbaismartinfra.com",
        "phone": "+91 22 2650 9100",
        "website": "https://www.mumbaismartinfra.com",
        "past_projects": json.dumps([
            {"title": "Mumbai 3D BIM-GIS City Digital Twin for Coastal Road Corridor", "client": "Brihanmumbai Municipal Corporation (BMC)", "value": "₹15.8 Cr"},
            {"title": "MMRDA Metro Line Subsurface Utility GPR Survey", "client": "Mumbai Metropolitan Region Development Authority", "value": "₹8.9 Cr"},
            {"title": "Thane Smart City Municipal GIS & Property Tax Survey", "client": "Thane Municipal Corporation", "value": "₹6.4 Cr"}
        ]),
        "synergy_roles": json.dumps(["BMC/MMRDA Urban Municipal Scope Demarcation", "3D City BIM-GIS Modeling", "Ground Penetrating Radar Utility Mapping"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Sahyadri Geo-Tech & Cadastral Labs",
        "short_name": "Sahyadri Geo-Tech",
        "primary_domain": "DGPS & Cadastral Ground Survey",
        "secondary_domains": json.dumps(["SVAMITVA Village Drone Support", "Highway DPR Surveys", "Revenue Land Record Resurvey", "Total Station Contour Surveys"]),
        "description": "Western Maharashtra's premier land survey and cadastral mapping consortium. Extensive track record with Pune, Nashik, Satara, and Kolhapur district collectorates on SVAMITVA village mapping and industrial land digitization.",
        "certifications": json.dumps(["Survey of India Empaneled", "Maharashtra PWD Approved", "ISO 9001:2015", "NABL Calibrated Equipment"]),
        "empanelment_status": "Maharashtra Land Records (Bhoomi Abhilekh) Class-A Empaneled",
        "turnover": "₹19.5 Cr (FY 2024-25)",
        "employee_count": "110 Field Surveyors & Bhoomi Abhilekh Cadastral Cartographers",
        "state": "Maharashtra",
        "city": "Pune",
        "pan_india_presence": True,
        "contact_person": "Pravin Deshmukh",
        "designation": "General Manager - Cadastral Operations",
        "email": "pravin@sahyadrigeotech.in",
        "phone": "+91 20 2544 3820",
        "website": "https://www.sahyadrigeotech.in",
        "past_projects": json.dumps([
            {"title": "Pune Ring Road Alignment & Cadastral Acquisition DGPS Survey", "client": "MSRDC", "value": "₹9.2 Cr"},
            {"title": "SVAMITVA Scheme Ground Resurvey of 600 Pune & Satara Villages", "client": "Survey of India / Maha Bhoomi Abhilekh", "value": "₹7.4 Cr"},
            {"title": "MIDC Industrial Area Topographic & Utility GIS", "client": "Maharashtra Industrial Development Corp", "value": "₹4.8 Cr"}
        ]),
        "synergy_roles": json.dumps(["Local Maharashtra Field Survey Crew", "Bhoomi Abhilekh Land Records Compliance", "DGPS Control Network Establishment"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Vidarbha Spatial Tech & Mining Solutions",
        "short_name": "Vidarbha Spatial",
        "primary_domain": "Mining Lease Demarcation & Forest Remote Sensing",
        "secondary_domains": json.dumps(["Open-Cast Mine Volumetric Survey", "Tadoba Corridor GIS", "Drone LiDAR for Forest Canopy", "DGPS Boundary Demarcation"]),
        "description": "Nagpur-based mining geospatial and forestry consultancy. Specializes in drone LiDAR volumetric audits for coal and manganese mines in Vidarbha, environmental clearance GIS, and wildlife corridor tracking.",
        "certifications": json.dumps(["Directorate of Geology and Mining (DGM) Approved", "ISO 9001:2015", "DGCA Certified UAV Operator"]),
        "empanelment_status": "Western Coalfields (WCL) & Maharashtra Forest Dept Empaneled",
        "turnover": "₹16.8 Cr (FY 2024-25)",
        "employee_count": "48 Mining Surveyors, Remote Sensing Analysts & Forest Rangers",
        "state": "Maharashtra",
        "city": "Nagpur",
        "pan_india_presence": True,
        "contact_person": "Dr. Shrikant Joshi",
        "designation": "Director - Mining & Forestry Bids",
        "email": "s.joshi@vidarbhaspatial.com",
        "phone": "+91 712 258 7410",
        "website": "https://www.vidarbhaspatial.com",
        "past_projects": json.dumps([
            {"title": "Chandrapur Open-Cast Coal Mine Quarterly Volumetric Drone Survey", "client": "Western Coalfields Limited (WCL)", "value": "₹6.8 Cr"},
            {"title": "Tadoba-Andhari Tiger Reserve Wildlife Corridor Satellite GIS", "client": "Maharashtra Forest Directorate", "value": "₹4.2 Cr"},
            {"title": "Nagpur Metro Phase-2 Corridor Pre-Construction Survey", "client": "Maha-Metro", "value": "₹5.1 Cr"}
        ]),
        "synergy_roles": json.dumps(["Mining Lease Volumetric LiDAR", "Maharashtra Forest Dept Clearances", "Local Vidarbha Engineering Survey"]),
        "rating": 4.7,
        "status": "Available"
    },
    {
        "name": "Nashik Agro-Spatial & Drone Mapping Services",
        "short_name": "Nashik Agro-Spatial",
        "primary_domain": "Agricultural Remote Sensing & Drone Mapping",
        "secondary_domains": json.dumps(["Crop Damage Satellite AI", "Canal Water Distribution GIS", "Soil Moisture Telemetry", "Vineyard & Horticulture Drone Analytics"]),
        "description": "Agro-tech and water resource spatial analytics enterprise in Nashik. Supports state crop insurance validation (PMFBY), Godavari basin canal command area mapping, and automated drone crop health diagnostics.",
        "certifications": json.dumps(["PMFBY Remote Sensing Partner", "ISO 9001:2015", "DGCA Drone Operator"]),
        "empanelment_status": "Maharashtra Department of Agriculture & Water Resources Empaneled",
        "turnover": "₹14.2 Cr (FY 2024-25)",
        "employee_count": "40 Agronomists, Drone Pilots & Spatial Analysts",
        "state": "Maharashtra",
        "city": "Nashik",
        "pan_india_presence": True,
        "contact_person": "Milind Kadam",
        "designation": "Head of Agri-Gov Alliances",
        "email": "milind.kadam@nashikagrospatial.in",
        "phone": "+91 253 231 8890",
        "website": "https://www.nashikagrospatial.in",
        "past_projects": json.dumps([
            {"title": "Godavari Canal Command Area GIS & Water Inflow Telemetry", "client": "Maharashtra Water Resources Dept", "value": "₹6.1 Cr"},
            {"title": "Kharif Crop Hailstorm Damage Assessment using Satellite & UAV Data", "client": "Govt of Maharashtra Agriculture Dept", "value": "₹4.8 Cr"}
        ]),
        "synergy_roles": json.dumps(["Agricultural AI & Crop Spectral Analytics", "Canal Command Area Water Modeling", "Local Ground-Truthing Field Teams"]),
        "rating": 4.7,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # KARNATAKA LOCAL VENDORS
    # -------------------------------------------------------------
    {
        "name": "Bengaluru Spatial AI & Tech Fab Pvt Ltd",
        "short_name": "Bengaluru Spatial AI",
        "primary_domain": "AI / Computer Vision & Geospatial Analytics",
        "secondary_domains": json.dumps(["BBMP Property Tax AI", "Smart Mobility GIS", "3D Building Footprint Extraction", "Deep Learning Change Detection"]),
        "description": "Specialized spatial AI research and software engineering studio in Bengaluru. Deep learning algorithms trained on BBMP municipal orthophotos for automated building polygon extraction, unauthorized construction detection, and traffic flow GIS.",
        "certifications": json.dumps(["NASSCOM DeepTech Certified", "ISO 27001", "CMMI Level 3", "Karnataka Innovation Partner"]),
        "empanelment_status": "KSRSAC & BBMP Empaneled Geospatial AI Vendor",
        "turnover": "₹26.5 Cr (FY 2024-25)",
        "employee_count": "75 Computer Vision Engineers & Geospatial Architects",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Kavitha Nambiar",
        "designation": "VP - Smart Governance & Geospatial AI",
        "email": "kavitha@blrspatialai.com",
        "phone": "+91 80 4912 6000",
        "website": "https://www.blrspatialai.com",
        "past_projects": json.dumps([
            {"title": "BBMP Property Tax Automated Building Footprint Extraction from 8cm Drone Imagery", "client": "Bruhat Bengaluru Mahanagara Palike (BBMP)", "value": "₹11.2 Cr"},
            {"title": "Statewide Road Asset AI Extraction from High-Res Satellite Imagery", "client": "Karnataka State Remote Sensing Applications Centre (KSRSAC)", "value": "₹7.8 Cr"},
            {"title": "Bengaluru Traffic Police Adaptive Signal Control GIS", "client": "Bengaluru Traffic Management Centre", "value": "₹5.4 Cr"}
        ]),
        "synergy_roles": json.dumps(["Computer Vision & AI Feature Extraction", "BBMP/KSRSAC Municipal Data Standards", "High-Volume Vector Data AI Processing"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Mysore Geo-Cadastre & Heritage Surveyors",
        "short_name": "Mysore Geo-Cadastre",
        "primary_domain": "DGPS & Cadastral Ground Survey",
        "secondary_domains": json.dumps(["Heritage 3D LiDAR", "MUDA Urban GIS", "Cauvery Water Telemetry", "Village Cadastral Demarcation"]),
        "description": "Established geospatial survey practice based in Mysuru. Key execution partner for MUDA master planning, Chamundi hill environmental 3D contour mapping, and rural cadastral resurvey across Old Mysore districts.",
        "certifications": json.dumps(["Survey of India Class-A Empaneled", "ISO 9001:2015", "State Revenue Certified"]),
        "empanelment_status": "Survey of India Karnataka Circle & Karnataka Revenue Dept Empaneled",
        "turnover": "₹15.8 Cr (FY 2024-25)",
        "employee_count": "70 Land Surveyors, Cadastral Drafters & Total Station Operators",
        "state": "Karnataka",
        "city": "Mysuru",
        "pan_india_presence": True,
        "contact_person": "Raghavendra Rao",
        "designation": "Managing Partner - Southern Karnataka Surveys",
        "email": "raghava@mysoregeocadastre.in",
        "phone": "+91 821 241 5590",
        "website": "https://www.mysoregeocadastre.in",
        "past_projects": json.dumps([
            {"title": "Mysuru Master Plan 2031 Comprehensive Land Use & Cadastral Survey", "client": "Mysuru Urban Development Authority (MUDA)", "value": "₹7.1 Cr"},
            {"title": "Cauvery River Basin Canal Sub-System DGPS Survey", "client": "Cauvery Neeravari Nigam Ltd (CNNL)", "value": "₹5.3 Cr"}
        ]),
        "synergy_roles": json.dumps(["Southern Karnataka Field Survey Mobilization", "Survey of India Ground Control GCP Alignment", "Heritage & Urban Planning Cadastral Models"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Deccan Drone Dynamics & Engineering Surveys",
        "short_name": "Deccan Drone Dynamics",
        "primary_domain": "Drone LiDAR & Aerial Mapping",
        "secondary_domains": json.dumps(["Corridor LiDAR Survey", "Highway DPR Topography", "Railway Track Alignment", "DGPS GCP Network"]),
        "description": "North Karnataka's largest aerial survey enterprise. Deploys heavy-payload LiDAR drones and dual-frequency GNSS networks for highway corridor DPRs, railway track doubling, and industrial corridor planning in Belagavi, Hubballi, and Ballari.",
        "certifications": json.dumps(["DGCA Type Certified Drone Fleet", "ISO 9001:2015", "Karnataka PWD Class-1 Empaneled"]),
        "empanelment_status": "DGCA Certified UAV Operator & Karnataka PWD Empaneled",
        "turnover": "₹20.4 Cr (FY 2024-25)",
        "employee_count": "55 Remote Pilots, Civil Engineers & LiDAR Analysts",
        "state": "Karnataka",
        "city": "Hubballi-Dharwad",
        "pan_india_presence": True,
        "contact_person": "Basavaraj Patil",
        "designation": "Director - Infrastructure Aerial Bids",
        "email": "basavaraj@deccandronedynamics.in",
        "phone": "+91 836 225 7800",
        "website": "https://www.deccandronedynamics.in",
        "past_projects": json.dumps([
            {"title": "Hubballi-Dharwad Smart City Corridor 3D LiDAR Survey", "client": "Hubballi-Dharwad Smart City Ltd (HDSCL)", "value": "₹6.9 Cr"},
            {"title": "Belagavi-Goa Greenfield Expressway Pre-Feasibility Aerial LiDAR", "client": "NHAI Project Implementation Unit", "value": "₹8.2 Cr"}
        ]),
        "synergy_roles": json.dumps(["North Karnataka Aerial LiDAR Operations", "Civil Infrastructure DPR Data Processing", "Local DGCA Pilot Crew Mobilization"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Malnad Ecological & Forestry Informatics",
        "short_name": "Malnad Eco-Informatics",
        "primary_domain": "Forest, Environmental & Carbon Assessment",
        "secondary_domains": json.dumps(["Western Ghats Biodiversity GIS", "Canopy Density Remote Sensing", "Wildlife Corridor Telemetry", "Catchment Area Modeling"]),
        "description": "Specialized forestry remote sensing and Western Ghats ecological consulting group. Conducts airborne LiDAR tree canopy height modeling, elephant corridor habitat suitability mapping, and river catchment studies.",
        "certifications": json.dumps(["MoEFCC Accredited Environmental Consultant", "QCI/NABET Accredited", "ISO 14001:2015"]),
        "empanelment_status": "Karnataka Forest Department & MoEFCC Empaneled",
        "turnover": "₹13.5 Cr (FY 2024-25)",
        "employee_count": "38 Ecologists, GIS Scientists & Forest Data Collectors",
        "state": "Karnataka",
        "city": "Mangaluru",
        "pan_india_presence": True,
        "contact_person": "Dr. Gururaj Hegde",
        "designation": "Lead Scientist - Forestry & Ecology",
        "email": "g.hegde@malnadeco.org",
        "phone": "+91 824 249 3320",
        "website": "https://www.malnadeco.org",
        "past_projects": json.dumps([
            {"title": "Western Ghats Eco-Sensitive Zone Forest Canopy & Biomass Estimation", "client": "Karnataka Forest Department", "value": "₹6.3 Cr"},
            {"title": "Kali River Hydroelectric Project Catchment Area Treatment (CAT) GIS", "client": "Karnataka Power Corporation Ltd (KPCL)", "value": "₹4.1 Cr"}
        ]),
        "synergy_roles": json.dumps(["Forest Canopy Modeling & Biomass Assessment", "NABET Accredited Ecological Clearances", "Local Forest Field Truthing Teams"]),
        "rating": 4.7,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # UTTAR PRADESH LOCAL VENDORS
    # -------------------------------------------------------------
    {
        "name": "Awadh Geo-Intelligence & Remote Sensing Ltd",
        "short_name": "Awadh Geo-Intel",
        "primary_domain": "GIS & Spatial Web Application Development",
        "secondary_domains": json.dumps(["RSAC-UP Spatial Integration", "UP Bhulekh Land Records GIS", "Smart Cities Geoportal", "Municipal Property Tax Portal"]),
        "description": "Uttar Pradesh's foremost GIS software engineering and geoportal development enterprise based in Lucknow. Empaneled with RSAC-UP and UPLC, having built state spatial decision support systems for urban local bodies, irrigation, and revenue departments.",
        "certifications": json.dumps(["CMMI Level 4", "ISO 9001:2015", "ISO 27001", "STQC Safe-to-Host Cleared", "UP Govt Empaneled IT Vendor"]),
        "empanelment_status": "Remote Sensing Applications Centre Uttar Pradesh (RSAC-UP) & UP Electronics Corp (UPLC) Empaneled",
        "turnover": "₹44.0 Cr (FY 2024-25)",
        "employee_count": "120 Full-Stack GIS Developers, Cartographers & Database Engineers",
        "state": "Uttar Pradesh",
        "city": "Lucknow",
        "pan_india_presence": True,
        "contact_person": "Akhilesh Srivastava",
        "designation": "Managing Director - State Government Engagements",
        "email": "alliances@awadhgeointel.com",
        "phone": "+91 522 405 8820",
        "website": "https://www.awadhgeointel.com",
        "past_projects": json.dumps([
            {"title": "Statewide WebGIS Geoportal & Land Parcel Registry Integration", "client": "RSAC-UP / UP Revenue Department", "value": "₹16.5 Cr"},
            {"title": "Lucknow Smart City Integrated Spatial MIS & Property Tax Dashboard", "client": "Lucknow Smart City Ltd (LSCL)", "value": "₹12.0 Cr"},
            {"title": "Gorakhpur Industrial Development Authority (GIDA) Master Plan GIS", "client": "GIDA UP", "value": "₹6.5 Cr"}
        ]),
        "synergy_roles": json.dumps(["RSAC-UP & UPLC Tender Qualifying Empanelment", "State Secretariat & Dept Technical Liaison", "Full-Stack Enterprise WebGIS & Database Dev"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Noida CyberSpatial MeitY Cloud Solutions",
        "short_name": "Noida CyberSpatial",
        "primary_domain": "MeitY-Empaneled Cloud & Data Center Infrastructure",
        "secondary_domains": json.dumps(["GovCloud Tier-3 Hosting", "STQC Security Auditing", "UPEIDA Expressway GIS Cloud", "High-Availability PostGIS Clusters"]),
        "description": "MeitY-empaneled data center and sovereign GovCloud provider located in Noida Sector 62. Dedicated government cloud zones powering UP state portals, UPEIDA expressway telemetry, and UP Police emergency GIS.",
        "certifications": json.dumps(["MeitY Empaneled Cloud Provider", "ISO 27001", "ISO 20000", "SOC-2 Type II", "CERT-In Empaneled Auditor"]),
        "empanelment_status": "MeitY Empaneled Sovereign GovCloud Tier-3 Provider",
        "turnover": "₹72.0 Cr (FY 2024-25)",
        "employee_count": "160 Cloud Architects, Cybersecurity Specialists & NOC Engineers",
        "state": "Uttar Pradesh",
        "city": "Noida",
        "pan_india_presence": True,
        "contact_person": "Vikrant Saxena",
        "designation": "Executive VP - GovCloud & Mission Mode Projects",
        "email": "v.saxena@noidacyberspatial.in",
        "phone": "+91 120 488 9200",
        "website": "https://www.noidacyberspatial.in",
        "past_projects": json.dumps([
            {"title": "Purvanchal & Bundelkhand Expressways Cloud GIS & Video Analytics Hosting", "client": "Uttar Pradesh Expressways Ind. Dev. Auth. (UPEIDA)", "value": "₹18.2 Cr"},
            {"title": "Statewide Land Information Management System High-Availability Cloud", "client": "UP Board of Revenue", "value": "₹14.0 Cr"}
        ]),
        "synergy_roles": json.dumps(["MeitY Tier-3 Sovereign Cloud Infrastructure", "STQC & CERT-In Security Clearance Guarantee", "High-Throughput Spatial Database Hosting"]),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Ganga Basin Hydro-Spatial Informatics Pvt Ltd",
        "short_name": "Ganga Hydro-Spatial",
        "primary_domain": "Water Resources, SCADA & IoT Telemetry",
        "secondary_domains": json.dumps(["Namami Gange River Telemetry", "Canal SCADA Automation", "Rural Piped Water (JJM) GIS", "Sewage Network Hydraulic Modeling"]),
        "description": "Specialized water resources and IoT engineering firm headquartered in Kanpur. Instrumental in Namami Gange telemetry monitoring, river water quality sensor arrays, and GIS-based asset mapping for UP Jal Nigam across 25+ districts.",
        "certifications": json.dumps(["Central Water Commission Empaneled", "ISO 9001:2015", "Jal Jeevan Mission Certified Partner"]),
        "empanelment_status": "National Mission for Clean Ganga (NMCG) & UP Jal Nigam Empaneled",
        "turnover": "₹28.5 Cr (FY 2024-25)",
        "employee_count": "80 Hydrologists, Instrumentation Engineers & GIS Technicians",
        "state": "Uttar Pradesh",
        "city": "Kanpur",
        "pan_india_presence": True,
        "contact_person": "Er. Alok Tripathi",
        "designation": "Director - Hydro & Municipal Infrastructure",
        "email": "alok.tripathi@gangahydro.in",
        "phone": "+91 512 254 3300",
        "website": "https://www.gangahydro.in",
        "past_projects": json.dumps([
            {"title": "Namami Gange Real-Time Water Quality & Inflow Telemetry Network (Kanpur-Prayagraj Stretch)", "client": "NMCG / UP Jal Nigam", "value": "₹13.4 Cr"},
            {"title": "Jal Jeevan Mission Rural Water Supply Pipeline GIS Asset Survey (12 Districts)", "client": "State Water & Sanitation Mission UP", "value": "₹9.8 Cr"}
        ]),
        "synergy_roles": json.dumps(["UP Jal Nigam Technical Empanelment Fulfill", "Hydraulic SCADA & River Basin Sensor Deployment", "Field Survey Crew in Eastern & Central UP"]),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Kashi Heritage GIS & Drone Mapping Services",
        "short_name": "Kashi Heritage GIS",
        "primary_domain": "Drone LiDAR & Aerial Mapping",
        "secondary_domains": json.dumps(["3D Heritage Conservation GIS", "Municipal Property Tax Drone Survey", "Pilgrimage Corridor Digital Twins", "DGPS Cadastral Resurvey"]),
        "description": "Eastern Uttar Pradesh's prominent drone survey and 3D digital heritage specialist. Created 3D LiDAR models of the 84 Varanasi ghats, Ayodhya temple corridors, and executed drone property tax surveys for Varanasi and Prayagraj municipal corporations.",
        "certifications": json.dumps(["DGCA Type Certified UAV Fleet", "ASI Heritage Survey Approved", "ISO 9001:2015"]),
        "empanelment_status": "Varanasi Smart City Ltd & MoHUA Empaneled Technical Consultant",
        "turnover": "₹18.0 Cr (FY 2024-25)",
        "employee_count": "50 Remote Pilots, Photogrammetry Specialists & Cadastral Crew",
        "state": "Uttar Pradesh",
        "city": "Varanasi",
        "pan_india_presence": True,
        "contact_person": "Manish Pandey",
        "designation": "Lead Partner - Aerial & Heritage Surveys",
        "email": "m.pandey@kashiheritagegis.org",
        "phone": "+91 542 222 6790",
        "website": "https://www.kashiheritagegis.org",
        "past_projects": json.dumps([
            {"title": "Varanasi Riverfront & 84 Ghats 3D LiDAR Digital Twin", "client": "Varanasi Smart City Ltd", "value": "₹8.5 Cr"},
            {"title": "Ayodhya Pilgrimage Master Plan 3D Aerial Survey & Corridor Simulation", "client": "Ayodhya Development Authority", "value": "₹6.8 Cr"},
            {"title": "Prayagraj Kumbh Mela Temporary Infrastructure & Pilgrim Flow GIS", "client": "Prayagraj Mela Authority", "value": "₹4.5 Cr"}
        ]),
        "synergy_roles": json.dumps(["Eastern UP Drone Flight Permits & Flight Ops", "3D Mesh & Heritage Conservation Modeling", "Local Varanasi/Ayodhya Municipal Liaison"]),
        "rating": 4.8,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # TELANGANA LOCAL VENDOR
    # -------------------------------------------------------------
    {
        "name": "Telangana Geo-Informatics & Spatial Infra Ltd",
        "short_name": "Telangana Geo-Infra",
        "primary_domain": "GIS & Spatial Web Application Development",
        "secondary_domains": json.dumps(["TRAC Spatial Integration", "Dharani Portal GIS", "GHMC Municipal GIS", "Canal Flow Telemetry"]),
        "description": "Premier Hyderabad-based GIS systems integrator and web portal development company. Direct partner for TRAC and GHMC municipal property surveys and irrigation canal command area mapping.",
        "certifications": json.dumps(["CMMI Level 4", "ISO 9001:2015", "ISO 27001", "Cert-In Audited"]),
        "empanelment_status": "Telangana Remote Sensing Applications Centre (TRAC) & GHMC Empaneled",
        "turnover": "₹34.0 Cr (FY 2024-25)",
        "employee_count": "95 Full-Stack Spatial Developers & Surveyors",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Srinivas Rao Goud",
        "designation": "Chief Strategy Officer",
        "email": "srinivas.rao@tggeoinfra.in",
        "phone": "+91 40 2311 4455",
        "website": "https://www.tggeoinfra.in",
        "past_projects": json.dumps([
            {"title": "Greater Hyderabad (GHMC) 3D Ward-Level Utility & Property Tax GIS", "client": "GHMC Hyderabad", "value": "₹12.5 Cr"},
            {"title": "Kaleshwaram Lift Irrigation Canal Network Real-Time Telemetry Geoportal", "client": "Irrigation Dept Govt of Telangana", "value": "₹10.2 Cr"}
        ]),
        "synergy_roles": json.dumps(["TRAC & GHMC Domain Authority", "Enterprise PostGIS & WebGIS Portal Engineering", "Telangana Regional On-Ground Coordination"]),
        "rating": 4.9,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # GUJARAT LOCAL VENDOR
    # -------------------------------------------------------------
    {
        "name": "Gujarat Spatial Solutions & Coastal Tech",
        "short_name": "Gujarat Spatial",
        "primary_domain": "Civil & Infrastructure Engineering Surveys",
        "secondary_domains": json.dumps(["BISAG-N Integration", "GIFT City Utility GPR", "Dholera SIR Cadastral Survey", "Industrial Port GIS"]),
        "description": "Specialized engineering and cadastral surveying firm based in Gandhinagar. Deep technical integration with BISAG-N, Dholera Special Investment Region (SIR), and Gujarat Maritime Board.",
        "certifications": json.dumps(["BISAG-N Technology Partner", "ISO 9001:2015", "NABL Calibrated"]),
        "empanelment_status": "BISAG-N & Gujarat Maritime Board Empaneled",
        "turnover": "₹25.0 Cr (FY 2024-25)",
        "employee_count": "65 Surveyors, Cartographers & Civil Engineers",
        "state": "Gujarat",
        "city": "Gandhinagar",
        "pan_india_presence": True,
        "contact_person": "Chirag Bhavesh Patel",
        "designation": "Director - Industrial Surveys",
        "email": "chirag.patel@gujaratspatial.in",
        "phone": "+91 79 2328 9910",
        "website": "https://www.gujaratspatial.in",
        "past_projects": json.dumps([
            {"title": "Dholera SIR Industrial Township DGPS Cadastral Demarcation", "client": "Dholera Industrial City Dev Ltd (DICDL)", "value": "₹8.8 Cr"},
            {"title": "GIFT City Subsurface Utility 3D GIS & GPR Mapping", "client": "Gujarat International Finance Tec-City (GIFT)", "value": "₹6.4 Cr"}
        ]),
        "synergy_roles": json.dumps(["BISAG-N Technical Collaboration", "Industrial Corridor & Town Planning Ground Surveys", "Local Gujarat Regulatory Approvals"]),
        "rating": 4.8,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # TAMIL NADU LOCAL VENDOR
    # -------------------------------------------------------------
    {
        "name": "Coromandel Drone & Cadastral Mapping Services",
        "short_name": "Coromandel Drones",
        "primary_domain": "Drone LiDAR & Aerial Mapping",
        "secondary_domains": json.dumps(["TNeGA Empaneled Drone Survey", "Coastal Erosion GIS", "River Basin LiDAR", "Industrial Park Topography"]),
        "description": "Tamil Nadu's premier aerial survey and photogrammetry operator based in Chennai. Executes statewide drone survey contracts for TNeGA, SIPCOT industrial corridors, and coastal erosion mapping for Tamil Nadu Water Resources Department.",
        "certifications": json.dumps(["DGCA Certified Drone Operator", "ISO 9001:2015", "TNeGA Registered Vendor"]),
        "empanelment_status": "Tamil Nadu e-Governance Agency (TNeGA) & PWD Tamil Nadu Empaneled",
        "turnover": "₹22.5 Cr (FY 2024-25)",
        "employee_count": "60 Remote Pilots, Photogrammetry Specialists & GIS Analysts",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "pan_india_presence": True,
        "contact_person": "S. Muthukumar",
        "designation": "Head of Operations - Government Tenders",
        "email": "muthukumar@coromandeldrones.in",
        "phone": "+91 44 2433 7700",
        "website": "https://www.coromandeldrones.in",
        "past_projects": json.dumps([
            {"title": "Statewide Drone Cadastral Survey for 750 Village Panchayats", "client": "TNeGA / Survey and Land Records TN", "value": "₹10.5 Cr"},
            {"title": "Cauvery Delta Irrigation Basin Aerial LiDAR Topography", "client": "PWD Water Resources Dept Tamil Nadu", "value": "₹7.2 Cr"}
        ]),
        "synergy_roles": json.dumps(["Tamil Nadu Drone Operations & Local DGCA Pilots", "TNeGA Platform Protocol Compliance", "Tamil Nadu District Land Records Verification"]),
        "rating": 4.8,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # RAJASTHAN LOCAL VENDOR
    # -------------------------------------------------------------
    {
        "name": "Thar Geo-Engineering & Mineral Survey Tech",
        "short_name": "Thar Geo-Tech",
        "primary_domain": "DGPS & Cadastral Ground Survey",
        "secondary_domains": json.dumps(["Mining Lease DGPS Demarcation", "Indira Gandhi Canal Telemetry", "Solar Park Topographic Survey", "Drone Volumetric Audit"]),
        "description": "Specialized mining and cadastral surveying organization in Rajasthan. Trusted partner for major solar power developers (Bhadla, Fatehgarh) and state mineral concession lease boundary demarcation.",
        "certifications": json.dumps(["Directorate of Mines & Geology Rajasthan Empaneled", "ISO 9001:2015", "Survey of India Western Zone Approved"]),
        "empanelment_status": "Rajasthan Mines & Geology Department Class-A Empaneled",
        "turnover": "₹18.5 Cr (FY 2024-25)",
        "employee_count": "55 Mining Surveyors, DGPS Operators & Cartographers",
        "state": "Rajasthan",
        "city": "Jaipur",
        "pan_india_presence": True,
        "contact_person": "Vikramaditya Rathore",
        "designation": "Director - Mining & Energy Survey Alliances",
        "email": "v.rathore@thargeotech.in",
        "phone": "+91 141 274 5500",
        "website": "https://www.thargeotech.in",
        "past_projects": json.dumps([
            {"title": "DGPS Demarcation & Digital Database of 450 Marble & Limestone Mining Leases", "client": "Dept of Mines & Geology, Govt of Rajasthan", "value": "₹8.5 Cr"},
            {"title": "Ultra Mega Solar Park (2,000 MW) Boundary & Contour Topographic Survey", "client": "Rajasthan Renewable Energy Corp (RRECL)", "value": "₹6.1 Cr"}
        ]),
        "synergy_roles": json.dumps(["Mining & Concession Demarcation Expertise", "Rajasthan Revenue & Mines Portal Compliance", "Desert Terrain Field Survey Logistics"]),
        "rating": 4.8,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # WEST BENGAL LOCAL VENDOR
    # -------------------------------------------------------------
    {
        "name": "Bengal Geo-Spatial & Riverine Survey Hub",
        "short_name": "Bengal Geo-Spatial",
        "primary_domain": "Water Resources, SCADA & IoT Telemetry",
        "secondary_domains": json.dumps(["Sundarbans Mangrove GIS", "Hooghly River Bathymetry", "Flood Inundation Early Warning", "Kolkata Municipal GIS"]),
        "description": "Leading hydrological surveying and environmental geospatial consultancy in West Bengal. Specialized in estuarine bathymetry, Sundarbans mangrove change detection, and tidal flood telemetry.",
        "certifications": json.dumps(["Central Water Commission Empaneled", "ISO 9001:2015", "NABET Accredited"]),
        "empanelment_status": "West Bengal Irrigation & Waterways Dept & WBSDI Empaneled",
        "turnover": "₹20.0 Cr (FY 2024-25)",
        "employee_count": "50 Hydrologists, Marine Surveyors & Remote Sensing Analysts",
        "state": "West Bengal",
        "city": "Kolkata",
        "pan_india_presence": True,
        "contact_person": "Soumitra Banerjee",
        "designation": "VP - Riverine & Environmental Systems",
        "email": "soumitra@bengalgeospatial.in",
        "phone": "+91 33 2465 8890",
        "website": "https://www.bengalgeospatial.in",
        "past_projects": json.dumps([
            {"title": "Hooghly Estuary Multi-Beam Bathymetric & Siltation Survey", "client": "Syama Prasad Mookerjee Port Trust (SMP Kolkata)", "value": "₹7.8 Cr"},
            {"title": "Sundarbans Biosphere Coastal Erosion & Mangrove Density Satellite GIS", "client": "West Bengal Forest Directorate", "value": "₹5.6 Cr"}
        ]),
        "synergy_roles": json.dumps(["Tidal & Estuarine Bathymetric Survey", "West Bengal State SDI Integration", "Eastern India Regional Logistics"]),
        "rating": 4.8,
        "status": "Available"
    },
    # -------------------------------------------------------------
    # MADHYA PRADESH LOCAL VENDOR
    # -------------------------------------------------------------
    {
        "name": "Central India Geo-Tech & Forest Informatics",
        "short_name": "Central India Geo-Tech",
        "primary_domain": "Forest, Environmental & Carbon Assessment",
        "secondary_domains": json.dumps(["MP Forest Dept GIS", "Kanha-Pench Corridor Mapping", "MPRRDA Rural Road Surveys", "Water Catchment GIS"]),
        "description": "Bhopal-based geospatial consultancy focusing on central Indian forestry, rural road surveys (MPRRDA), and catchment area treatment studies. Direct empanelment with MAPIT and Madhya Pradesh Forest Directorate.",
        "certifications": json.dumps(["MAPIT Empaneled IT Vendor", "MoEFCC Accredited", "ISO 9001:2015"]),
        "empanelment_status": "Madhya Pradesh Forest Department & MAPIT Empaneled",
        "turnover": "₹17.5 Cr (FY 2024-25)",
        "employee_count": "45 Ecologists, Remote Sensing Specialists & DGPS Surveyors",
        "state": "Madhya Pradesh",
        "city": "Bhopal",
        "pan_india_presence": True,
        "contact_person": "Dharmendra Chouhan",
        "designation": "Director - Forestry & State Alliances",
        "email": "d.chouhan@centralindiageotech.org",
        "phone": "+91 755 277 4410",
        "website": "https://www.centralindiageotech.org",
        "past_projects": json.dumps([
            {"title": "Madhya Pradesh Statewide Tiger Corridor & Eco-Sensitive Zone GIS", "client": "Madhya Pradesh Forest Department", "value": "₹8.2 Cr"},
            {"title": "PMGSY Rural Road Network Asset Mapping for 1,200 km", "client": "MP Rural Road Development Authority (MPRRDA)", "value": "₹5.9 Cr"}
        ]),
        "synergy_roles": json.dumps(["Central India Forest Survey & Ground Truthing", "MAPIT Technical Standards Fulfill", "Bhopal Operations & State Liaison"]),
        "rating": 4.8,
        "status": "Available"
    }
]


def ensure_partners_seeded(db: Session):
    """Seed initial partners if table is empty, and sync any missing seed entries dynamically."""
    # Ensure tables exist
    models.Base.metadata.create_all(bind=db.get_bind())
    
    existing_partners = db.query(models.Partner.name).all()
    existing_names = {p[0] for p in existing_partners}

    added = False
    for p_data in INITIAL_PARTNERS_SEED:
        if p_data["name"] not in existing_names:
            partner = models.Partner(**p_data)
            db.add(partner)
            existing_names.add(p_data["name"])
            added = True

    if added:
        db.commit()


def get_all_partners(
    db: Session,
    search: Optional[str] = None,
    domain: Optional[str] = None,
    state: Optional[str] = None,
    certification: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> List[models.Partner]:
    """Retrieve and filter partners from database."""
    ensure_partners_seeded(db)
    query = db.query(models.Partner)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Partner.name.ilike(search_pattern),
                models.Partner.short_name.ilike(search_pattern),
                models.Partner.primary_domain.ilike(search_pattern),
                models.Partner.secondary_domains.ilike(search_pattern),
                models.Partner.description.ilike(search_pattern),
                models.Partner.certifications.ilike(search_pattern),
                models.Partner.city.ilike(search_pattern),
                models.Partner.state.ilike(search_pattern),
                models.Partner.contact_person.ilike(search_pattern)
            )
        )

    if domain and domain.upper() != "ALL":
        query = query.filter(
            or_(
                models.Partner.primary_domain.ilike(f"%{domain}%"),
                models.Partner.secondary_domains.ilike(f"%{domain}%")
            )
        )

    if state and state.upper() != "ALL":
        query = query.filter(
            or_(
                models.Partner.state.ilike(f"%{state}%"),
                models.Partner.pan_india_presence == True
            )
        )

    if certification and certification.upper() != "ALL":
        query = query.filter(models.Partner.certifications.ilike(f"%{certification}%"))

    if status and status.upper() != "ALL":
        query = query.filter(models.Partner.status == status)

    return query.order_by(models.Partner.rating.desc(), models.Partner.name.asc()).offset(skip).limit(limit).all()


def compute_partner_match(tender: models.Tender, partner: models.Partner) -> Dict[str, Any]:
    """
    Intelligently calculate match score, category, and specific 'why needed' rationale
    for a collaboration partner based on the tender's title, department, description, state, and keywords.
    """
    tender_title = (tender.title or "").lower()
    tender_desc = (tender.description or "").lower()
    tender_dept = (tender.department or "").lower()
    tender_state = (tender.state.name or "") if tender.state else ""
    tender_keywords = [k.keyword.lower() for k in tender.keywords] if tender.keywords else []

    tender_text = f"{tender_title} {tender_desc} {tender_dept} {' '.join(tender_keywords)} {tender_state.lower()}"

    p_domain = (partner.primary_domain or "").lower()
    p_sec = (partner.secondary_domains or "").lower()
    p_certs = (partner.certifications or "").lower()
    p_desc = (partner.description or "").lower()
    p_name = (partner.name or "").lower()

    base_score = 65.0
    matched_reasons = []
    synergies = []

    # Domain match rules
    if "drone" in p_domain or "lidar" in p_domain or "aerial" in p_domain:
        if any(term in tender_text for term in ["drone", "lidar", "aerial", "uav", "svamitva", "photogrammetry", "ortho"]):
            base_score += 26.0
            matched_reasons.append("Mandatory requirement for DGCA Type-Certified drones and calibrated LiDAR payloads")
            synergies.append("Partner provides DGCA-certified flight crew & raw LiDAR collection; GISFY conducts spatial analytics & geoportal integration")
        elif any(term in tender_text for term in ["survey", "mapping", "topographic", "contour"]):
            base_score += 15.0
            matched_reasons.append("Airborne aerial mapping capability complements ground survey requirements")
            synergies.append("Accelerates topographic data capture via high-speed drone corridor passes")

    if "satellite" in p_domain or "remote sensing" in p_domain:
        if any(term in tender_text for term in ["satellite", "remote sensing", "imagery", "spectral", "vegetation", "crop", "earth observation"]):
            base_score += 28.0
            matched_reasons.append("Direct source for sub-meter commercial optical & SAR radar satellite imagery")
            synergies.append("Partner licenses and orthorectifies 30cm Maxar/Planet constellations; GISFY models change detection workflows")
        elif any(term in tender_text for term in ["forest", "water", "agriculture", "climate", "environment"]):
            base_score += 17.0
            matched_reasons.append("Multi-temporal satellite monitoring required for large-scale natural resource tracking")
            synergies.append("Provides historical satellite baseline and quarterly vegetation indices")

    if "cloud" in p_domain or "meity" in p_domain:
        if any(term in tender_text for term in ["cloud", "hosting", "data center", "server", "ict", "security audit", "stqc", "storage"]):
            base_score += 29.0
            matched_reasons.append("Fulfills RFP mandatory criterion for MeitY-empaneled sovereign GovCloud Tier-3/4 hosting")
            synergies.append("Partner manages STQC-cleared sovereign data center infrastructure; GISFY deploys application containers & WebGIS")
        elif any(term in tender_text for term in ["software", "portal", "geoportal", "mis", "application", "website", "digital"]):
            base_score += 18.0
            matched_reasons.append("High-availability enterprise hosting infrastructure required for public-facing state portals")
            synergies.append("Provides 99.95% uptime SLA and disaster recovery replication")

    if "cadastral" in p_domain or "dgps" in p_domain:
        if any(term in tender_text for term in ["cadastral", "dgps", "total station", "boundary", "land records", "revenue", "demarcation"]):
            base_score += 28.0
            matched_reasons.append("Survey of India Class-A certified field teams with 50+ DGPS rovers for ground boundary demarcation")
            synergies.append("Partner mobilizes field ground survey crews in districts; GISFY handles cartographic validation & database digitization")
        elif any(term in tender_text for term in ["survey", "topographic", "road", "railway", "pipeline"]):
            base_score += 16.0
            matched_reasons.append("Ground control network (GCP) establishment for engineering survey accuracy")
            synergies.append("Executes dual-frequency GNSS baseline calibration for ground control")

    if "ai" in p_domain or "vision" in p_domain:
        if any(term in tender_text for term in ["ai", "machine learning", "deep learning", "automation", "feature extraction", "analytics"]):
            base_score += 27.0
            matched_reasons.append("Automated AI computer vision pipelines for high-throughput building footprint & asset detection")
            synergies.append("Partner trains neural models for automated extraction; GISFY validates topology and delivers shapefiles")
        elif any(term in tender_text for term in ["smart city", "property", "encroachment", "change detection"]):
            base_score += 15.0
            matched_reasons.append("AI anomaly detection for rapid property identification and encroachment alerts")
            synergies.append("Automates municipal property tax discrepancy checks from drone imagery")

    if "water" in p_domain or "scada" in p_domain:
        if any(term in tender_text for term in ["water", "irrigation", "canal", "river", "hydrology", "scada", "dam", "flood", "drainage"]):
            base_score += 29.0
            matched_reasons.append("Central Water Commission (CWC) empaneled partner with calibrated ultrasonic flow & telemetry sensors")
            synergies.append("Partner deploys IoT field telemetry & hydraulic modeling (HEC-RAS); GISFY builds command center dashboards")
        elif any(term in tender_text for term in ["smart city", "utility", "environmental"]):
            base_score += 14.0
            matched_reasons.append("Water network spatial monitoring and storm water drainage modeling expertise")
            synergies.append("Supplies sensor nodes and telemetry interfaces for urban hydrological monitoring")

    if "smart city" in p_domain or "municipal" in p_domain:
        if any(term in tender_text for term in ["smart city", "municipal", "property tax", "urban", "ulb", "town planning", "3d city"]):
            base_score += 28.0
            matched_reasons.append("MoHUA empaneled consultant experienced in 3D Digital Twin city models & municipal property tax revenue")
            synergies.append("Partner leads door-to-door property enumeration & municipal domain; GISFY implements the WebGIS portal")
        elif any(term in tender_text for term in ["gis", "mapping", "survey"]):
            base_score += 13.0
            matched_reasons.append("Extensive municipal administrative data models and Urban Local Body (ULB) integration")
            synergies.append("Ensures compliance with National Urban Information System (NUIS) standards")

    if "forest" in p_domain or "environmental" in p_domain:
        if any(term in tender_text for term in ["forest", "environment", "wildlife", "climate", "carbon", "ecology", "eia", "biodiversity"]):
            base_score += 29.0
            matched_reasons.append("QCI/NABET accredited environmental consultancy & Forest Survey of India research expertise")
            synergies.append("Partner executes ecological field sampling and carbon stock assessment; GISFY provides spatial modeling")
        elif any(term in tender_text for term in ["remote sensing", "satellite", "water"]):
            base_score += 14.0
            matched_reasons.append("Vegetation density indices and catchment area treatment planning support")
            synergies.append("Analyzes spectral bands for watershed environmental impact assessments")

    if "civil" in p_domain or "infra" in p_domain:
        if any(term in tender_text for term in ["civil", "highway", "road", "railway", "dpr", "bridge", "corridor", "pavement", "pwd"]):
            base_score += 26.0
            matched_reasons.append("NHAI and RDSO approved engineering consultancy with heavy geotechnical and corridor survey rigs")
            synergies.append("Partner delivers engineering DPR and cross-section profiles; GISFY delivers alignment WebGIS")
        elif any(term in tender_text for term in ["survey", "cctv", "construction"]):
            base_score += 12.0
            matched_reasons.append("Civil infrastructure and site layout engineering expertise")
            synergies.append("Provides certified civil surveyor stamps and structural site clearance")

    if "equipment" in p_domain or "sensor" in p_domain:
        if any(term in tender_text for term in ["equipment", "sensor", "hardware", "calibration", "mobile lidar", "sounder", "instrument"]):
            base_score += 27.0
            matched_reasons.append("GeM Star OEM seller providing high-accuracy mobile LiDAR vehicle rigs and NABL calibration certificates")
            synergies.append("Partner guarantees zero-downtime sensor hardware leasing; GISFY operates survey crews & post-processes data")
        elif any(term in tender_text for term in ["lidar", "drone", "survey"]):
            base_score += 15.0
            matched_reasons.append("NABL-calibrated instruments ensure compliance with strict RFP instrument accuracy limits")
            synergies.append("Supplies backup mobile LiDAR scanners and laser receiver pods")

    if any(t in p_domain for t in ["gis & spatial web", "geoportal", "software development", "web application"]):
        if any(term in tender_text for term in ["software", "portal", "geoportal", "mis", "application", "database", "web", "dashboard", "development", "it", "ict", "digital"]):
            base_score += 27.0
            matched_reasons.append("State IT & Electronics Development Corp empaneled CMMI-certified GIS development partner")
            synergies.append("Partner co-develops backend modules and spatial database connectors; GISFY leads core proposals & frontend portal")

    if "hydrographic" in p_domain or "marine" in p_domain or "coastal" in p_domain:
        if any(term in tender_text for term in ["coastal", "marine", "bathymetric", "port", "hydrographic", "ocean", "harbour", "estuary"]):
            base_score += 28.0
            matched_reasons.append("National Hydrographic Office (NHO) certified bathymetric echo sounding & coastal zone mapping")
            synergies.append("Partner executes marine sonar transects; GISFY renders 3D bathymetric mesh & coastal erosion models")

    if "mining" in p_domain or "mineral" in p_domain:
        if any(term in tender_text for term in ["mining", "mineral", "lease", "geology", "quarry", "excavation", "coal"]):
            base_score += 27.0
            matched_reasons.append("Dept of Mines & Geology empaneled partner with DGPS concession lease demarcation and volumetric LiDAR")
            synergies.append("Partner conducts pit volumetric drone mapping; GISFY provides reconciliation GIS reports")

    if "agriculture" in p_domain or "agro" in p_domain or "crop" in p_domain:
        if any(term in tender_text for term in ["agriculture", "crop", "farming", "pmfby", "soil", "horticulture", "agri"]):
            base_score += 27.0
            matched_reasons.append("State Agriculture Dept empaneled partner for PMFBY satellite crop yield & drought assessment")
            synergies.append("Partner collects ground-truthing crop spectral samples; GISFY models satellite vegetation anomaly maps")

    if "consortium" in p_domain or "turnkey" in p_domain:
        # High financial turnover lead partner
        base_score += 18.0
        matched_reasons.append("₹88+ Cr turnover fulfills high financial qualifying criteria & provides Bank Guarantee / EMD backing")
        synergies.append("Partner acts as Lead Bidder / Consortium Financial Sponsor; GISFY executes complete geospatial technical delivery")

    # State geographic bonus
    if partner.state and tender_state and partner.state.lower() == tender_state.lower():
        base_score += 9.0
        matched_reasons.append(f"Local state vendor with operational branch & ground presence in {tender_state}")
    elif partner.pan_india_presence:
        base_score += 3.0

    # Ensure score bounds
    final_score = min(98.5, max(62.0, base_score))
    # Round to 1 decimal
    final_score = round(final_score, 1)

    # Classify category
    if final_score >= 90.0:
        match_cat = "⭐ Tier 1 Lead Match"
    elif final_score >= 80.0:
        match_cat = "💎 High Synergy JV Partner"
    elif final_score >= 70.0:
        match_cat = "🤝 Technical Specialist Partner"
    else:
        match_cat = "🛠️ Supporting OEM / Equipment Partner"

    # Fallback reasons if generic
    if not matched_reasons:
        matched_reasons.append(f"Provides complementary specialized capabilities in {partner.primary_domain}")
    if not synergies:
        synergies.append(f"Collaborates with GISFY in a Joint Venture (JV) combining GISFY's GIS platform with {partner.short_name or partner.name}'s technical domain")

    why_needed = f"Key Requirement for Tender #{tender.tender_id}: " + "; ".join(matched_reasons[:2]) + "."
    synergy_scope = "; ".join(synergies[:2]) + "."

    return {
        "match_score": final_score,
        "match_category": match_cat,
        "why_needed": why_needed,
        "synergy_scope": synergy_scope
    }


def search_partners_for_tender(
    db: Session,
    tender_id: int,
    query_str: Optional[str] = None,
    domain_filter: Optional[str] = None,
    min_score: Optional[float] = 80.0
) -> Dict[str, Any]:
    """
    Find and rank collaboration partners for a specific tender.
    By default filters to show only high matches (score >= 80%).
    """
    ensure_partners_seeded(db)

    tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not tender:
        return {"error": "Tender not found", "matched_partners": []}

    partners = get_all_partners(db, search=query_str, domain=domain_filter, limit=150)

    # Load any existing collaboration status overrides for this tender
    collab_records = db.query(models.TenderCollaboration).filter(models.TenderCollaboration.tender_id == tender.id).all()
    collab_map = {c.partner_id: c for c in collab_records}

    matched_results = []
    for p in partners:
        match_info = compute_partner_match(tender, p)
        collab_rec = collab_map.get(p.id)
        
        status = collab_rec.status if collab_rec else "Recommended"
        notes = collab_rec.notes if collab_rec else None

        partner_dict = {
            "id": p.id,
            "name": p.name,
            "short_name": p.short_name,
            "primary_domain": p.primary_domain,
            "secondary_domains": p.secondary_domains,
            "description": p.description,
            "certifications": p.certifications,
            "empanelment_status": p.empanelment_status,
            "turnover": p.turnover,
            "employee_count": p.employee_count,
            "state": p.state,
            "city": p.city,
            "pan_india_presence": p.pan_india_presence,
            "contact_person": p.contact_person,
            "designation": p.designation,
            "email": p.email,
            "phone": p.phone,
            "website": p.website,
            "past_projects": p.past_projects,
            "synergy_roles": p.synergy_roles,
            "rating": p.rating,
            "status": p.status,
            "match_score": match_info["match_score"],
            "match_category": match_info["match_category"],
            "why_needed": match_info["why_needed"],
            "synergy_scope": match_info["synergy_scope"],
            "collaboration_status": status,
            "collaboration_notes": notes
        }
        matched_results.append(partner_dict)

    # Sort by match score descending
    matched_results.sort(key=lambda x: x["match_score"], reverse=True)

    # Filter to only show high matches (score >= min_score, e.g. 80%)
    if min_score is not None and min_score > 0:
        filtered_results = [p for p in matched_results if p["match_score"] >= min_score]
    else:
        filtered_results = matched_results

    return {
        "tender": {
            "id": tender.id,
            "tender_id": tender.tender_id,
            "title": tender.title,
            "department": tender.department,
            "state_name": tender.state.name if tender.state else "Pan-India",
            "published_date": tender.published_date.isoformat() if tender.published_date else None,
            "last_date": tender.last_date.isoformat() if tender.last_date else None,
            "portal_tender_url": tender.portal_tender_url,
            "keywords": [k.keyword for k in tender.keywords] if tender.keywords else []
        },
        "total_matched": len(filtered_results),
        "total_candidates": len(matched_results),
        "min_score": min_score,
        "partners": filtered_results
    }


def update_tender_collaboration(
    db: Session,
    tender_id: int,
    partner_id: int,
    status: str,
    notes: Optional[str] = None
) -> models.TenderCollaboration:
    """Update or create a collaboration status entry between tender and partner."""
    collab = db.query(models.TenderCollaboration).filter(
        models.TenderCollaboration.tender_id == tender_id,
        models.TenderCollaboration.partner_id == partner_id
    ).first()

    if not collab:
        collab = models.TenderCollaboration(
            tender_id=tender_id,
            partner_id=partner_id,
            status=status,
            notes=notes
        )
        db.add(collab)
    else:
        collab.status = status
        if notes is not None:
            collab.notes = notes
        collab.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(collab)
    return collab


def generate_outreach_proposal(db: Session, payload: schemas.OutreachProposalRequest) -> Dict[str, Any]:
    """Generate a formal Letter of Intent (LOI) & JV proposal to collaborate on a specific tender."""
    tender = db.query(models.Tender).filter(models.Tender.id == payload.tender_id).first()
    if not tender:
        raise ValueError(f"Tender with ID {payload.tender_id} not found.")

    partner = db.query(models.Partner).filter(models.Partner.id == payload.partner_id).first()
    if not partner:
        raise ValueError(f"Partner with ID {payload.partner_id} not found.")

    match_info = compute_partner_match(tender, partner)
    state_name = tender.state.name if tender.state else "India"
    dept_name = tender.department or f"State Government of {state_name}"
    due_date_str = tender.last_date.strftime("%d %b %Y, %I:%M %p") if tender.last_date else "As per official portal notice"

    subject = f"[Consortium / JV Opportunity] Tender #{tender.tender_id} - {state_name}: Collaboration with GISFY"

    letter_text = f"""CONFIDENTIAL & PRIVILEGED — LETTER OF INTENT FOR CONSORTIUM / JOINT VENTURE

Date: {datetime.utcnow().strftime('%d %B %Y')}

To:
{partner.contact_person or 'Head of Strategic Alliances'}
{partner.designation or 'Director - Govt Tenders & Partnerships'}
{partner.name}
{partner.city or ''}, {partner.state or 'India'}
Email: {partner.email or 'N/A'} | Phone: {partner.phone or 'N/A'}

From:
{payload.gisfy_contact_name}
GISFY (Spatial Intelligence & Automated Proposals Directorate)
Hyderabad, India
Email: {payload.gisfy_contact_email} | Web: https://gisfy.co.in

Subject: Invitation for Joint Venture / Consortium Bidding for Tender Ref #{tender.tender_id}
Tender Title: {tender.title}
Authority / Department: {dept_name}
State: {state_name}
Submission Due Date: {due_date_str}

Dear {partner.contact_person or 'Partner Team'},

GISFY is actively preparing our bid response for the above-referenced prestigious tender published by {dept_name}. Based on our automated proposal intelligence analysis and eligibility cross-matching, we identify {partner.name} as our preferred high-synergy collaboration partner.

1. COLLABORATION RATIONALE & WHY NEEDED:
{match_info['why_needed']}

2. PROPOSED CONSORTIUM / JV ARCHITECTURE:
- Proposed Structure: {payload.proposed_jv_split}
- GISFY Core Scope: Turnkey Bid Management, WebGIS Portal Architecture, Spatial Database Integration, PostGIS Engine, Cloud Solution Design, and Quality Assurance.
- {partner.name} Scope: {match_info['synergy_scope']}

3. STRATEGIC SYNERGY:
By uniting GISFY's proprietary geospatial proposal intelligence and {partner.name}'s market-leading domain credentials ({partner.primary_domain}, {partner.empanelment_status or 'Industry Certifications'}), our joint consortium fulfills 100% of the technical, turnover, and empanelment eligibility benchmarks.

{f"4. ADDITIONAL NOTES FROM GISFY BID TEAM:\n{payload.custom_message}\n" if payload.custom_message else ""}
5. IMMEDIATE ACTION & NEXT STEPS:
We invite you to sign a mutual Non-Disclosure Agreement (NDA) and schedule a joint technical alignment call within the next 48 hours to finalize scope demarcation, joint costing, and submission formalities before the deadline ({due_date_str}).

Please confirm your availability and interest by replying directly to this communication.

Warm regards,

{payload.gisfy_contact_name}
GISFY Tendering & Strategic Alliances Division
Email: {payload.gisfy_contact_email}
"""

    # Update collaboration status in DB to 'Outreach Sent'
    update_tender_collaboration(db, tender.id, partner.id, status="Outreach Sent", notes=f"Outreach generated on {datetime.utcnow().strftime('%d %b %Y')}")

    return {
        "partner_id": partner.id,
        "partner_name": partner.name,
        "partner_email": partner.email,
        "tender_id": str(tender.tender_id),
        "tender_title": tender.title,
        "state_name": state_name,
        "department": tender.department,
        "due_date": due_date_str,
        "subject": subject,
        "proposal_letter": letter_text,
        "collaboration_status": "Outreach Sent"
    }


def get_collaboration_stats(db: Session) -> Dict[str, Any]:
    """Return summary analytics for collaboration partners."""
    ensure_partners_seeded(db)
    total_partners = db.query(models.Partner).count()
    total_collabs = db.query(models.TenderCollaboration).count()
    
    # Active domains
    domains = db.query(models.Partner.primary_domain).distinct().all()
    domain_list = [d[0] for d in domains if d[0]]

    # Status counts
    active_outreach = db.query(models.TenderCollaboration).filter(models.TenderCollaboration.status.in_(["Outreach Sent", "In Discussion", "NDA Signed", "Partnered"])).count()

    return {
        "total_partners": total_partners,
        "total_domains": len(domain_list),
        "domains": domain_list,
        "active_collaborations": total_collabs,
        "active_outreach_count": active_outreach,
        "top_partners": [
            {"id": p.id, "name": p.name, "domain": p.primary_domain, "rating": p.rating, "turnover": p.turnover, "state": p.state}
            for p in db.query(models.Partner).order_by(models.Partner.rating.desc()).limit(6)
        ]
    }
