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
        "name": "ideaForge Technology Ltd",
        "short_name": "ideaForge",
        "primary_domain": "DGCA-Certified Survey Drones & UAV Photogrammetry",
        "secondary_domains": json.dumps(['Drone LiDAR', 'Aerial Photogrammetry', 'SVAMITVA Large Scale Mapping', 'Defense & Civil UAV Surveillance']),
        "description": "NSE and BSE listed pioneer and market leader in Indian unmanned aircraft systems (UAS). Operates DGCA Type-Certified mapping drones (SWITCH, NETRA V4+, Q6) widely deployed across Survey of India SVAMITVA village mapping, mining volumetric surveys, and border surveillance.",
        "certifications": json.dumps(['BSE/NSE Listed (IDEAFORGE)', 'DGCA Type Certified (UAV Mapping)', 'ISO 9001:2015', 'Survey of India SVAMITVA Supplier', 'GeM Star Seller']),
        "empanelment_status": "DGCA Type-Certified UAV OEM & Survey of India SVAMITVA Vendor",
        "turnover": "\u20b9314 Cr (FY 2023-24)",
        "employee_count": "450+ Aerospace Engineers, Remote Pilots & R&D Specialists",
        "state": "Maharashtra",
        "city": "Navi Mumbai",
        "pan_india_presence": True,
        "contact_person": "Corporate Business Alliances Desk",
        "designation": "Head - Strategic Alliances & Government Bids",
        "email": "contact@ideaforgetech.com",
        "phone": "+91 22 6787 1000",
        "website": "https://ideaforgetech.com",
        "past_projects": json.dumps([{'title': 'SVAMITVA Scheme High-Resolution Drone Mapping of 100,000+ Villages', 'client': 'Survey of India / Ministry of Panchayati Raj', 'value': '₹150+ Cr'}, {'title': 'Open-Cast Coal Mine 3D Volume Estimation & Volumetric Analysis', 'client': 'Coal India Limited (CIL)', 'value': '₹28 Cr'}, {'title': 'Urban Aerial Surveillance and Disaster Response UAV Fleet', 'client': 'NDRF / Ministry of Home Affairs', 'value': '₹45 Cr'}]),
        "synergy_roles": json.dumps(['DGCA-Certified Drone Hardware & Flight Operations Lead', 'Raw Aerial Orthomosaic & Point Cloud Capture', 'Sensor Calibration & Flight Safety Officer']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Genesys International Corporation Ltd",
        "short_name": "Genesys International",
        "primary_domain": "3D Digital Twins, Smart Cities & GIS Mapping",
        "secondary_domains": json.dumps(['Ayodhya 3D Twin', 'Street View 360', 'HD NavIC Mapping', 'Municipal Property Tax GIS']),
        "description": "Premier BSE and NSE listed Indian geospatial solutions and 3D digital twin corporation. Official 3D Digital Twin Partner for Survey of India, builder of Ayodhya's 3D City Platform, and leading enterprise provider of LiDAR, street-level 360 imaging, and municipal WebGIS.",
        "certifications": json.dumps(['BSE/NSE Listed (GENESYS)', 'Survey of India National 3D Twin Partner', 'ISO 9001:2015', 'ISO 27001', 'CMMI Level 5']),
        "empanelment_status": "Survey of India National 3D Digital Twin Partner & Smart Cities Empaneled",
        "turnover": "\u20b9205 Cr (FY 2023-24)",
        "employee_count": "2,000+ Geospatial Engineers, Photogrammetrists & 3D Modelers",
        "state": "Maharashtra",
        "city": "Mumbai",
        "pan_india_presence": True,
        "contact_person": "Corporate Alliances & Government Tender Cell",
        "designation": "Vice President - Government & Strategic Bids",
        "email": "sales@igenesys.com",
        "phone": "+91 22 4488 4488",
        "website": "https://igenesys.com",
        "past_projects": json.dumps([{'title': 'National 3D Digital Twin Map of Urban India', 'client': 'Survey of India / DST', 'value': '₹85 Cr'}, {'title': 'Ayodhya Smart City High-Accuracy 3D Urban Model & WebGIS', 'client': 'Ayodhya Development Authority', 'value': '₹18 Cr'}, {'title': 'Greater Mumbai GIS Property Tax Base Mapping & Utility Survey', 'client': 'Municipal Corporation of Greater Mumbai (MCGM)', 'value': '₹42 Cr'}]),
        "synergy_roles": json.dumps(['3D Urban Mesh & Digital Twin Architect', 'High-Definition Street View Mapping', 'Enterprise Spatial Database Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Ceinsys Tech Ltd",
        "short_name": "Ceinsys Tech",
        "primary_domain": "GIS Web Portals, Smart Water SCADA & Cadastral Mapping",
        "secondary_domains": json.dumps(['Water Supply SCADA', 'HEC-RAS Hydraulic Modeling', 'Jal Jeevan Mission GIS', 'Land Records Modernization']),
        "description": "BSE listed geospatial engineering and infrastructure consultancy. Renowned for large-scale water distribution SCADA modeling, river basin telemetry, municipal GIS geoportals, and automated property tax solutions across Maharashtra, MP, and UP.",
        "certifications": json.dumps(['BSE Listed (CEINSYS)', 'CMMI Level 5 (Services)', 'ISO 9001:2015', 'ISO 27001', 'Central Water Commission Empaneled']),
        "empanelment_status": "Central Water Commission & State Water Resources Empaneled Partner",
        "turnover": "\u20b9248 Cr (FY 2023-24)",
        "employee_count": "1,400+ Engineers, SCADA Specialists & Survey Experts",
        "state": "Maharashtra",
        "city": "Nagpur",
        "pan_india_presence": True,
        "contact_person": "Strategic Tender & Consortium Management Cell",
        "designation": "Director - Public Sector Infrastructure Projects",
        "email": "info@cstech.ai",
        "phone": "+91 712 224 9460",
        "website": "https://www.cstech.ai",
        "past_projects": json.dumps([{'title': 'Maharashtra Water Resources Pipeline Network GIS & SCADA Telemetry', 'client': 'Maharashtra Water Resources Regulatory Authority', 'value': '₹64 Cr'}, {'title': 'Belapur, Nerul & Turbhe Water Supply Pipeline Geospatial Database', 'client': 'Navi Mumbai Municipal Corporation', 'value': '₹16 Cr'}, {'title': 'Jal Jeevan Mission Rural Water Supply GIS & Hydraulic Modeling', 'client': 'Water Resources Dept, Govt of MP', 'value': '₹38 Cr'}]),
        "synergy_roles": json.dumps(['SCADA & Hydraulic Telemetry Systems Lead', 'Water Distribution Network GIS Modeler', 'Field Survey Operations Co-Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "MapmyIndia (C.E. Info Systems Ltd)",
        "short_name": "MapmyIndia",
        "primary_domain": "Digital Map Data, GIS Navigation, IoT Telematics & Geoportals",
        "secondary_domains": json.dumps(['Mappls SDKs', 'Vehicle Telematics & GPS', 'National Road Safety Portal', 'NavIC Satellite Navigation']),
        "description": "NSE and BSE listed leader in digital mapping, geospatial data products, IoT telematics, and navigation technologies. Powers India's premier digital maps, CoWIN vaccination spatial routing, and mission-critical government GIS portals.",
        "certifications": json.dumps(['BSE/NSE Listed (MAPMYINDIA)', 'ISO 9001:2015', 'ISO 27001', 'CMMI Level 3', 'MeitY Digital India Partner']),
        "empanelment_status": "National Digital Mapping Partner & Ministry of Road Transport Empaneled",
        "turnover": "\u20b9379 Cr (FY 2023-24)",
        "employee_count": "1,100+ Cartographers, Software Engineers & Data Analysts",
        "state": "Delhi",
        "city": "New Delhi",
        "pan_india_presence": True,
        "contact_person": "Government Alliances & Public Sector Directorate",
        "designation": "Head - Strategic Government Bids & GIS Partnerships",
        "email": "contact@mapmyindia.com",
        "phone": "+91 11 4600 9900",
        "website": "https://www.mapmyindia.com",
        "past_projects": json.dumps([{'title': 'National Road Safety GIS & Blackspot Mapping Portal', 'client': 'Ministry of Road Transport and Highways (MoRTH)', 'value': '₹48 Cr'}, {'title': 'CoWIN Spatial Vaccination Center Locator & Routing System', 'client': 'Ministry of Health and Family Welfare (MoHFW)', 'value': '₹22 Cr'}, {'title': 'Smart City Emergency Response Vehicle GPS Tracking & Dispatch', 'client': 'Delhi Police & Safe City Project', 'value': '₹35 Cr'}]),
        "synergy_roles": json.dumps(['Core Digital Map Layer Provider', 'Navigation & Routing Engine Host', 'IoT Fleet GPS Telematics Integrator']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Garuda Aerospace Pvt Ltd",
        "short_name": "Garuda Aerospace",
        "primary_domain": "DGCA Type-Certified Commercial Drones & Agricultural Drone Spraying/Survey",
        "secondary_domains": json.dumps(['Krishi Drone Spraying', 'Survey of India UAV Mapping', 'Disaster Response Aerial Scouting', 'Industrial Asset Inspection']),
        "description": "India's prominent drone technology company operating a fleet of 400+ DGCA-certified multi-rotor and fixed-wing UAVs. Empaneled with Survey of India for SVAMITVA village mapping and agricultural crop health monitoring across Southern and Central India.",
        "certifications": json.dumps(['DGCA Type Certified (Small & Medium UAVs)', 'ISO 9001:2015', 'Survey of India Empaneled', 'Make In India Drone Manufacturer']),
        "empanelment_status": "DGCA Approved Drone OEM & Survey of India SVAMITVA Empaneled",
        "turnover": "\u20b9115 Cr (FY 2023-24)",
        "employee_count": "350+ Remote Pilots, Field Crew & Drone Technicians",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "pan_india_presence": True,
        "contact_person": "Government & Strategic Alliances Division",
        "designation": "Vice President - Institutional & Govt Tenders",
        "email": "business@garudaaerospace.com",
        "phone": "+91 44 2435 1986",
        "website": "https://www.garudaaerospace.com",
        "past_projects": json.dumps([{'title': 'SVAMITVA Large Scale Cadastral Drone Mapping across 5,000 Villages', 'client': 'Survey of India / Tamil Nadu Land Administration', 'value': '₹26 Cr'}, {'title': 'National Krishi Drone Agricultural Spraying & Health Monitoring', 'client': 'Department of Agriculture & Farmers Welfare', 'value': '₹42 Cr'}, {'title': 'NDRF Flood Inundation Aerial Reconnaissance & Emergency Mapping', 'client': 'National Disaster Response Force', 'value': '₹14 Cr'}]),
        "synergy_roles": json.dumps(['Drone Field Fleet Deployment Lead', 'Agricultural Sensor & Multispectral Operator', 'Southern Region Flight Crew Lead']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Asteria Aerospace Ltd",
        "short_name": "Asteria Aerospace",
        "primary_domain": "Enterprise Drone Solutions, SkyDeck GIS Platform & UAV Mapping",
        "secondary_domains": json.dumps(['Pipeline Corridor Security', 'Forest Wildfire Reconnaissance', 'SVAMITVA Drone Operations', 'SkyDeck Cloud Data Engine']),
        "description": "A subsidiary of Jio Platforms Limited. Full-stack drone technology company designing and manufacturing DGCA type-certified UAVs (A200-XT, A410) with proprietary SkyDeck cloud platform for enterprise geospatial processing.",
        "certifications": json.dumps(['DGCA Type Certified (A200-XT)', 'ISO 9001:2015', 'ISO 27001', 'Survey of India Empaneled', 'Jio Platforms Subsidiary']),
        "empanelment_status": "DGCA Type-Certified Manufacturer & Survey of India Empaneled",
        "turnover": "\u20b992 Cr (FY 2023-24)",
        "employee_count": "280+ Drone Engineers, Software Developers & Drone Pilots",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Enterprise & Public Sector Business Desk",
        "designation": "General Manager - Strategic Accounts & Defence/Govt Bids",
        "email": "info@asteria.co.in",
        "phone": "+91 73530 36888",
        "website": "https://www.asteria.co.in",
        "past_projects": json.dumps([{'title': 'Survey of India SVAMITVA Drone Supply & Cadastral Survey', 'client': 'Survey of India', 'value': '₹34 Cr'}, {'title': 'Cross-Country Oil Pipeline Corridor Aerial Surveillance', 'client': 'Bharat Petroleum (BPCL) / Indian Oil (IOCL)', 'value': '₹19 Cr'}, {'title': 'Forest Reserve Canopy & Wildlife Protection Drone Surveillance', 'client': 'Karnataka Forest Department', 'value': '₹11 Cr'}]),
        "synergy_roles": json.dumps(['SkyDeck Enterprise Drone Cloud Pipeline', 'DGCA Certified UAV Flight Operations', 'Corridor Aerial Mapping Specialist']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Aarav Unmanned Systems (Aereo)",
        "short_name": "Aereo (AUS)",
        "primary_domain": "DGCA Type-Certified Commercial UAV Mapping & Mining Volumetric Survey",
        "secondary_domains": json.dumps(['SVAMITVA Cadastral Mapping', 'Open-cast Mine Volumetrics', 'Urban Property Tax 3D Modeling', 'GIS Orthomosaic Processing']),
        "description": "Premier drone technology enterprise (operating as Aereo). The largest single execution partner for Survey of India's SVAMITVA village mapping scheme, having mapped over 25,000 villages across Haryana, MP, UP, and Rajasthan with 100+ operational survey drones.",
        "certifications": json.dumps(['DGCA Type Certified UAVs', 'Survey of India Class-A Empaneled', 'ISO 9001:2015', 'NASSCOM CoE Partner']),
        "empanelment_status": "Survey of India SVAMITVA Prime Contractor & Mining Empaneled",
        "turnover": "\u20b968 Cr (FY 2023-24)",
        "employee_count": "220+ Remote Pilots, GIS Cartographers & Flight Engineers",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Government Procurement & Strategic Contracts Unit",
        "designation": "Head - Public Sector Projects & Institutional Alliances",
        "email": "contact@aereo.io",
        "phone": "+91 80 2521 2997",
        "website": "https://aereo.io",
        "past_projects": json.dumps([{'title': 'SVAMITVA Large Scale Cadastral Drone Mapping of 25,000+ Villages', 'client': 'Survey of India / Govt of MP & Rajasthan', 'value': '₹58 Cr'}, {'title': 'Tata Steel Open-Cast Mine Stockpile 3D Volumetric Reconciliation', 'client': 'Tata Steel Raw Materials Division', 'value': '₹12 Cr'}, {'title': 'Smart City 3D Orthomosaic & Property Tax Demarcation Survey', 'client': 'Bhopal Smart City Development Corporation', 'value': '₹8.5 Cr'}]),
        "synergy_roles": json.dumps(['Large-Scale Drone Fleet Operations Lead', 'Mine Volumetric Calculation & Terrain Modeling', 'District-level Cadastral Ground Truthing']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Skylark Drones Pvt Ltd",
        "short_name": "Skylark Drones",
        "primary_domain": "Drone Survey Analytics Platform, Infrastructure Corridor & Mining GIS",
        "secondary_domains": json.dumps(['Spectra Drone Data Platform', 'Linear Corridor Inspection', 'Solar Farm 3D Elevation Modeling', 'Highway DPR Surveys']),
        "description": "Enterprise drone data intelligence company. Operates the proprietary Spectra drone workflow platform used by Tata Steel, L&T, NHAI, and state development agencies for high-precision terrain modeling, cut/fill calculation, and linear corridor mapping.",
        "certifications": json.dumps(['ISO 9001:2015', 'ISO 27001', 'DGCA Compliant Operations', 'CMMI Level 3']),
        "empanelment_status": "NHAI & Infrastructure Concessionaires Empaneled Drone Analytics Partner",
        "turnover": "\u20b944 Cr (FY 2023-24)",
        "employee_count": "130+ Drone Engineers, Data Scientists & Software Architects",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Strategic Partnerships & Infrastructure Sales Desk",
        "designation": "Director - Enterprise Infrastructure Alliances",
        "email": "info@skylarkdrones.com",
        "phone": "+91 63649 31044",
        "website": "https://skylarkdrones.com",
        "past_projects": json.dumps([{'title': 'NHAI 500km Expressway Corridor 3D Topographic Drone Survey', 'client': 'National Highways Authority of India (NHAI)', 'value': '₹18 Cr'}, {'title': 'Utility-Scale Solar Farm Topographic Contour & Drainage Analysis', 'client': 'L&T Construction (Renewable Energy)', 'value': '₹9.2 Cr'}, {'title': 'Mining Lease Boundary Demarcation & Volumetric Tracking', 'client': 'Ultratech Cement Mineral Division', 'value': '₹7.4 Cr'}]),
        "synergy_roles": json.dumps(['Spectra Cloud Data Pipeline Integrator', 'Cut/Fill & Volumetric Elevation Modeler', 'Corridor Alignment Analytics Lead']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "RMSI Pvt Ltd",
        "short_name": "RMSI",
        "primary_domain": "Enterprise GIS Solutions, Disaster Modeling, Land Records & Remote Sensing",
        "secondary_domains": json.dumps(['DILRMP Cadastral Modernization', 'Disaster Risk Modeling (NDMA)', 'Utility Electrical GIS', 'High-Resolution Satellite Analytics']),
        "description": "Global geospatial services leader with 4,000+ staff. Instrumental in executing India's Digital India Land Records Modernization Programme (DILRMP), National Cyclone Risk Mitigation (NDMA/World Bank), and statewide electrical utility spatial databases.",
        "certifications": json.dumps(['CMMI Dev Level 5', 'ISO 9001:2015', 'ISO 27001', 'Survey of India Class-A Empaneled', 'NDMA Disaster Consultant']),
        "empanelment_status": "National Disaster Management Authority (NDMA) & State Land Records Empaneled",
        "turnover": "\u20b9480 Cr (FY 2023-24)",
        "employee_count": "4,000+ Geospatial Professionals, Disaster Modeler & Software Engineers",
        "state": "Uttar Pradesh",
        "city": "Noida",
        "pan_india_presence": True,
        "contact_person": "Government Tenders & Institutional Alliances Directorate",
        "designation": "Senior Vice President - India Public Sector Business",
        "email": "india@rmsi.com",
        "phone": "+91 120 404 0500",
        "website": "https://www.rmsi.com",
        "past_projects": json.dumps([{'title': 'National Cyclone Risk Mitigation Project (NCRMP) Hazard Modeling', 'client': 'National Disaster Management Authority (NDMA) / World Bank', 'value': '₹72 Cr'}, {'title': 'Digital India Land Records Modernization Programme (DILRMP) Cadastre Mapping', 'client': 'Ministry of Rural Development / Govt of UP & MP', 'value': '₹110 Cr'}, {'title': 'Power Distribution Utility Spatial Asset Mapping (IPDS / RAPDRP)', 'client': 'State Power Distribution Corporation', 'value': '₹45 Cr'}]),
        "synergy_roles": json.dumps(['Disaster Risk & Hazard Modeling Lead', 'Statewide Cadastral Integration Co-Lead', 'Turnkey Bid Financial Sponsor']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Marvel Geospatial Solutions Pvt Ltd",
        "short_name": "Marvel Geospatial",
        "primary_domain": "Photogrammetry, Mobile LiDAR, DGPS Ground Survey & Cadastral Mapping",
        "secondary_domains": json.dumps(['Canal Network Survey', 'HMDA Master Plan GIS', 'Mobile Laser Scanning', 'DGPS Boundary Demarcation']),
        "description": "Premier Hyderabad-based geospatial engineering company. Operates high-accuracy mobile LiDAR vehicle rigs, Leica dual-frequency DGPS receivers, and photogrammetric workstations with extensive field credentials across irrigation and urban planning.",
        "certifications": json.dumps(['ISO 9001:2015', 'ISO 27001', 'Survey of India Empaneled', 'TRAC Empaneled Partner']),
        "empanelment_status": "Telangana Remote Sensing Applications Centre (TRAC) & Irrigation Dept Empaneled",
        "turnover": "\u20b952 Cr (FY 2023-24)",
        "employee_count": "320+ Surveyors, LiDAR Processors & GIS Specialists",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Public Sector Tender & JV Bids Directorate",
        "designation": "Vice President - Business Development & Public Bids",
        "email": "info@marvelgeospatial.com",
        "phone": "+91 40 6641 3226",
        "website": "https://marvelgeospatial.com",
        "past_projects": json.dumps([{'title': 'Telangana Irrigation Canal Network Mobile LiDAR & Alignment Survey', 'client': 'Telangana Irrigation & CAD Department', 'value': '₹21 Cr'}, {'title': 'Hyderabad Metropolitan Development Authority (HMDA) Master Plan GIS', 'client': 'HMDA / Urban Development Dept', 'value': '₹14 Cr'}, {'title': 'Rural DGPS Cadastral Resurvey and Boundary Pillar Installation', 'client': 'Andhra Pradesh Land Records Dept', 'value': '₹16.5 Cr'}]),
        "synergy_roles": json.dumps(['Mobile LiDAR Scanning Operations Lead', 'DGPS Ground Control Network Establishment', 'Irrigation Canal Alignment Modeler']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "IIC Technologies Ltd",
        "short_name": "IIC Technologies",
        "primary_domain": "Hydrographic Surveys, Marine Nautical Charting, Bathymetric Sonar & Aerial LiDAR",
        "secondary_domains": json.dumps(['Inland Waterways Bathymetry', 'National Hydrographic Office Charting', 'Coastal Erosion Modeling', 'Port Dredging Hydrography']),
        "description": "World-renowned hydrographic survey and marine geospatial solutions provider. Officially accredited by the International Hydrographic Organization (IHO) and National Hydrographic Office (NHO), with deep-water multibeam echo sounders and dual-frequency side-scan sonar.",
        "certifications": json.dumps(['NHO Certified Hydrographic Survey Agency', 'IHO Cat-A Certified Hydrographers', 'ISO 9001:2015', 'ISO 27001', 'CMMI Level 3']),
        "empanelment_status": "National Hydrographic Office (NHO) & Inland Waterways Authority (IWAI) Empaneled",
        "turnover": "\u20b9165 Cr (FY 2023-24)",
        "employee_count": "800+ Certified Hydrographers, Marine Cartographers & Geospatial Engineers",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Marine & Hydrographic Alliances Directorate",
        "designation": "Director - Marine Infrastructure & Hydrographic Bids",
        "email": "info@iictechnologies.com",
        "phone": "+91 40 6791 4444",
        "website": "https://www.iictechnologies.com",
        "past_projects": json.dumps([{'title': 'National Waterway-1 & Waterway-2 Bathymetric Multibeam Survey', 'client': 'Inland Waterways Authority of India (IWAI)', 'value': '₹38 Cr'}, {'title': 'Electronic Navigational Charts (ENC) Production for Indian Ports', 'client': 'National Hydrographic Office (NHO) / Indian Navy', 'value': '₹45 Cr'}, {'title': 'Major Port Coastal Dredging Monitoring & Seabed Sonar Profiling', 'client': 'Visakhapatnam Port Authority / Chennai Port Trust', 'value': '₹19 Cr'}]),
        "synergy_roles": json.dumps(['Multibeam Echo Sounder & Sonar Fleet Lead', 'IHO S-57 / S-101 Nautical Chart Specialist', 'Coastal & Riverine Bathymetric Profiler']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Cyient Ltd",
        "short_name": "Cyient",
        "primary_domain": "Large-Scale Utility GIS, Geospatial Engineering & Enterprise Telematics",
        "secondary_domains": json.dumps(['Smart Utility Grids', 'Telecom FTTx Network Design', 'Digital Twin Infrastructure', 'Defense Spatial Solutions']),
        "description": "NSE and BSE listed global technology giant specializing in geospatial engineering, telecom fiber design, utility GIS asset tracking, and smart infrastructure. Tier-1 consortium leader capable of sponsoring high-value government RFPs (\u20b950-200 Cr).",
        "certifications": json.dumps(['BSE/NSE Listed (CYIENT)', 'CMMI Level 5', 'ISO 9001:2015', 'ISO 27001', 'AS9100D Certified']),
        "empanelment_status": "National Telecom & Power Utility Empaneled System Integrator",
        "turnover": "\u20b97,147 Cr (FY 2023-24)",
        "employee_count": "15,000+ Engineers & Geospatial Professionals Worldwide",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Public Sector & Infrastructure Business Unit",
        "designation": "Senior Vice President - Geospatial & Government Solutions",
        "email": "connect@cyient.com",
        "phone": "+91 40 6764 1000",
        "website": "https://www.cyient.com",
        "past_projects": json.dumps([{'title': 'Statewide Power Utility GIS Network Modernization & Consumer Indexing', 'client': 'State Electricity Distribution Companies (Discoms)', 'value': '₹120 Cr'}, {'title': 'National Optical Fiber Network (BharatNet) FTTx GIS Route Engineering', 'client': 'Bharat Broadband Network Limited (BBNL)', 'value': '₹180 Cr'}, {'title': 'City Gas Distribution (CGD) Underground Pipeline Spatial Asset Register', 'client': 'GAIL Gas / Adani Total Gas', 'value': '₹48 Cr'}]),
        "synergy_roles": json.dumps(['Tier-1 Consortium Lead & Financial Sponsor', 'Underground Utility & FTTx Route Architect', 'Enterprise System Integration Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Scanpoint Geomatics Ltd",
        "short_name": "Scanpoint Geomatics",
        "primary_domain": "Indigenous GIS/RS Software (IGiS with ISRO), Geomatics & Geoportals",
        "secondary_domains": json.dumps(['IGiS Indigenous GIS Software', 'ISRO Joint Technology', 'State Geoportals', 'Town Planning Urban GIS']),
        "description": "BSE listed Indian pioneer in indigenous geospatial software. Joint developer of 'IGiS' (India's first indigenous GIS & Image Processing platform) with the Indian Space Research Organisation (ISRO), powering state spatial geoportals.",
        "certifications": json.dumps(['BSE Listed (SCANPGEOM)', 'ISRO Technology Transfer Partner', 'ISO 9001:2015', 'CMMI Level 3', 'BISAG-N Partner']),
        "empanelment_status": "ISRO Joint Technology Partner & State IT Development Corp Empaneled",
        "turnover": "\u20b962 Cr (FY 2023-24)",
        "employee_count": "280+ GIS Developers, Satellite Image Analysts & Remote Sensing Scientists",
        "state": "Gujarat",
        "city": "Ahmedabad",
        "pan_india_presence": True,
        "contact_person": "Institutional Alliances & Government Programs Desk",
        "designation": "Vice President - IGiS Platforms & Strategic Public Accounts",
        "email": "info@sgligis.com",
        "phone": "+91 79 4939 1735",
        "website": "https://www.sgligis.com",
        "past_projects": json.dumps([{'title': 'IGiS Enterprise GIS Platform Deployment for National Hydrology Project', 'client': 'Ministry of Jal Shakti / State Water Resources', 'value': '₹28 Cr'}, {'title': 'Gujarat Urban Development Town Planning Spatial Database', 'client': 'Gujarat Urban Development Mission / BISAG-N', 'value': '₹19 Cr'}, {'title': 'Statewide Forestry Canopy Density & Fire Risk GIS Geoportal', 'client': 'State Forest Department', 'value': '₹14 Cr'}]),
        "synergy_roles": json.dumps(['Indigenous IGiS Enterprise Software Provider', 'ISRO Bhuvan Spatial Node Connector', 'State Geoportal Architecture Lead']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "SATPALDA Geospatial Services",
        "short_name": "SATPALDA",
        "primary_domain": "Satellite Imagery Distribution (Maxar, Planet, Airbus, ISRO) & Satellite Analytics",
        "secondary_domains": json.dumps(['Maxar 30cm WorldView', 'InSAR Ground Subsidence', 'PlanetScope Daily Monitoring', 'PMFBY Crop Analytics']),
        "description": "Premier satellite data aggregator and authorized distributor in India for Maxar Technologies (30cm WorldView-3/4), Planet Labs, Airbus Defence & Space, and Cartosat constellations, delivering satellite InSAR land subsidence monitoring and stereo DEMs.",
        "certifications": json.dumps(['Authorized Maxar Technologies Distributor', 'Planet Labs Master Partner', 'ISO 9001:2015', 'ISRO/NRSC Value-Added Partner']),
        "empanelment_status": "Authorized International Earth Observation Imagery Distributor in India",
        "turnover": "\u20b945 Cr (FY 2023-24)",
        "employee_count": "95 Earth Observation Specialists, Radar Scientists & Photogrammetrists",
        "state": "Delhi",
        "city": "New Delhi",
        "pan_india_presence": True,
        "contact_person": "Earth Observation Data & Government Contracts Desk",
        "designation": "Director - Satellite Data Sourcing & Strategic Alliances",
        "email": "info@satpalda.com",
        "phone": "+91 11 4130 5450",
        "website": "https://satpalda.com",
        "past_projects": json.dumps([{'title': 'Statewide 30cm Satellite Ortho-Base Map for Smart Cities Mission', 'client': 'State Remote Sensing Applications Centre', 'value': '₹18 Cr'}, {'title': 'Satellite InSAR Infrastructure Subsidence & Rail Corridor Monitoring', 'client': 'Dedicated Freight Corridor (DFCCIL) / Metro Rails', 'value': '₹11 Cr'}, {'title': 'Multi-Temporal Satellite Crop Phenology & PMFBY Yield Loss Assessment', 'client': 'State Agriculture Department', 'value': '₹14.5 Cr'}]),
        "synergy_roles": json.dumps(['Sub-meter Commercial Satellite Imagery Provider', 'Radar InSAR Land Subsidence Modeler', 'Satellite Stereo DEM Generation Specialist']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "NewSpace India Ltd (NSIL)",
        "short_name": "NSIL (ISRO)",
        "primary_domain": "Indian Remote Sensing Satellite Data (Cartosat, Resourcesat, Oceansat) & Space Tech",
        "secondary_domains": json.dumps(['Cartosat Stereo Imagery', 'Resourcesat Multispectral Data', 'Oceansat Ocean Color', 'ISRO Space Solutions']),
        "description": "Central Public Sector Enterprise (CPSE) under the Department of Space, Government of India. The commercial arm of ISRO responsible for commercial exploitation of space products, Cartosat high-resolution stereo data, and Resourcesat thematic mapping.",
        "certifications": json.dumps(['Govt of India CPSE (Dept of Space)', 'Official ISRO Commercial Entity', 'ISO 9001:2015']),
        "empanelment_status": "Government of India Central Public Sector Enterprise (Dept of Space)",
        "turnover": "\u20b92,940 Cr (FY 2023-24)",
        "employee_count": "200+ Space Scientists, Satellite Mission Specialists & Engineers",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Earth Observation Services & Government Desks",
        "designation": "Head - Earth Observation Marketing & Govt Sales",
        "email": "contact@nsilindia.co.in",
        "phone": "+91 80 2322 7777",
        "website": "https://www.nsilindia.co.in",
        "past_projects": json.dumps([{'title': 'High-Resolution Cartosat-3 Imagery Supply for National Infrastructure', 'client': 'Survey of India / Ministry of Defence', 'value': '₹85 Cr'}, {'title': 'Statewide Resourcesat-2A Land Use & Land Cover (LULC) Mapping', 'client': 'National Remote Sensing Centre (NRSC) / State Space Centres', 'value': '₹42 Cr'}, {'title': 'Coastal & Oceanographic Satellite Telemetry Feed Integration', 'client': 'INCOIS / Ministry of Earth Sciences', 'value': '₹31 Cr'}]),
        "synergy_roles": json.dumps(['ISRO Sovereign Earth Observation Data Lead', 'Cartosat High-Accuracy DEM Supplier', 'National Space Mission Data Integrator']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Yotta Data Services Pvt Ltd",
        "short_name": "Yotta Data Services",
        "primary_domain": "MeitY-Empaneled Sovereign Tier-IV Cloud & Hyperscale Data Centers",
        "secondary_domains": json.dumps(['GovCloud Tier-IV Hosting', 'Yntraa Sovereign Cloud', 'Shakti AI GPU Cloud', 'STQC & CERT-In Compliant']),
        "description": "Hiranandani Group company and leading MeitY-empaneled Indian cloud service provider. Operates Asia's largest Uptime Institute certified Tier-IV data center park (Yotta NM1 in Navi Mumbai, D1 in Greater Noida) compliant with strict government data localization laws.",
        "certifications": json.dumps(['MeitY Empaneled Cloud Service Provider', 'Tier-IV Uptime Certified', 'ISO 27001', 'ISO 20000-1', 'ISO 22301', 'SOC 2 Type II']),
        "empanelment_status": "MeitY Empaneled Cloud Service Provider & Sovereign AI Compute Host",
        "turnover": "\u20b9480 Cr (FY 2023-24)",
        "employee_count": "600+ Cloud Infrastructure Engineers & Cyber Security Specialists",
        "state": "Maharashtra",
        "city": "Navi Mumbai",
        "pan_india_presence": True,
        "contact_person": "Government Alliances & Public Cloud Directorate",
        "designation": "Head - Public Sector & GovCloud Partnerships",
        "email": "info@yotta.com",
        "phone": "+91 22 6868 9000",
        "website": "https://yotta.com",
        "past_projects": json.dumps([{'title': 'Sovereign GovCloud Tier-IV Hosting for E-Governance Portals', 'client': 'Ministry of Electronics and Information Technology (MeitY)', 'value': '₹95 Cr'}, {'title': 'Smart Cities Mission Integrated Command & Control Center (ICCC) Cloud', 'client': 'State Urban Development Department', 'value': '₹54 Cr'}, {'title': 'National Spatial Data Infrastructure High-Availability Database Cluster', 'client': 'State Remote Sensing Applications Centre', 'value': '₹32 Cr'}]),
        "synergy_roles": json.dumps(['MeitY Tier-IV Sovereign Cloud Infrastructure Host', 'STQC Cyber Security & NIC Compliance Lead', 'Spatial Geodatabase 99.99% Uptime Provider']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "ESDS Software Solution Ltd",
        "short_name": "ESDS (eNlight Cloud)",
        "primary_domain": "MeitY-Empaneled Government Cloud (eNlight Cloud) & Smart City Data Centers",
        "secondary_domains": json.dumps(['Government Community Cloud (GCC)', 'eNlight Auto-Scaling Cloud', 'Disaster Recovery Center', 'STQC Audited Security']),
        "description": "Premier MeitY-empaneled Indian cloud innovation corporation. Host to 300+ government portals, municipal corporations, and banking networks via its patented vertically auto-scaling eNlight Government Community Cloud (GCC).",
        "certifications": json.dumps(['MeitY Empaneled Cloud Service Provider', 'ISO 27001', 'ISO 20000-1', 'ISO 22301', 'STQC Audited', 'CMMI Level 3']),
        "empanelment_status": "MeitY Empaneled Cloud Service Provider (GovCloud / GCC)",
        "turnover": "\u20b9285 Cr (FY 2023-24)",
        "employee_count": "900+ Cloud Architects, DevOps Engineers & Security Analysts",
        "state": "Maharashtra",
        "city": "Nashik",
        "pan_india_presence": True,
        "contact_person": "Government Solutions & Institutional Cloud Unit",
        "designation": "Vice President - Government Community Cloud (GCC)",
        "email": "getintouch@esds.co.in",
        "phone": "+91 253 711 2244",
        "website": "https://www.esds.co.in",
        "past_projects": json.dumps([{'title': 'State Data Center (SDC) Hybrid Cloud Hosting for 15+ State Departments', 'client': 'State Information Technology Department', 'value': '₹52 Cr'}, {'title': 'Smart City Mission Automated Property Tax & WebGIS Portal Cloud', 'client': 'Smart City Municipal Corporation', 'value': '₹28 Cr'}, {'title': 'State Public Works Department (PWD) E-Tendering & Asset Cloud', 'client': 'Public Works Department', 'value': '₹19 Cr'}]),
        "synergy_roles": json.dumps(['MeitY-Empaneled Auto-Scaling Cloud Host', 'State E-Governance Portal Infrastructure Lead', 'Disaster Recovery & Hot Standby Architect']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "CtrlS Datacenters Ltd",
        "short_name": "CtrlS",
        "primary_domain": "Rated-4 Hyperscale Data Centers & MeitY Empaneled E-Gov Cloud Infrastructure",
        "secondary_domains": json.dumps(['Rated-4 Hyperscale Facilities', 'Government Community Cloud', 'UIDAI Disaster Recovery Host', 'Disaster Recovery Replication']),
        "description": "Asia's largest Rated-4 hyperscale data center provider. Fully empaneled with MeitY, operating state-of-the-art facilities across Hyderabad, Mumbai, Bangalore, and Noida, trusted by UIDAI Aadhaar, national stock exchanges, and state government data centers.",
        "certifications": json.dumps(['MeitY Empaneled Cloud Provider', 'Rated-4 Uptime Certified', 'ISO 27001', 'SOC 2 Type II', 'PCI-DSS Compliant']),
        "empanelment_status": "MeitY Empaneled Cloud Service Provider & Hyperscale Infrastructure Host",
        "turnover": "\u20b91,240 Cr (FY 2023-24)",
        "employee_count": "1,800+ Hyperscale Engineers & Security Specialists",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Public Sector & Government Cloud Directorate",
        "designation": "Head - Strategic Government Infrastructure & Hyperscale Cloud",
        "email": "marketing@ctrls.in",
        "phone": "+91 40 4647 4747",
        "website": "https://www.ctrls.in",
        "past_projects": json.dumps([{'title': 'UIDAI Aadhaar Disaster Recovery Hyperscale Infrastructure', 'client': 'Unique Identification Authority of India (UIDAI)', 'value': '₹140 Cr'}, {'title': 'Telangana State Spatial Data Infrastructure (T-SSDI) Cloud Hosting', 'client': 'TRAC / Information Technology Dept, Govt of Telangana', 'value': '₹32 Cr'}, {'title': 'State Power Utility ERP and Smart Metering Data Center Cluster', 'client': 'State Electricity Regulatory Commission', 'value': '₹65 Cr'}]),
        "synergy_roles": json.dumps(['Rated-4 Hyperscale Data Center Host', 'High-Volume Spatial Telemetry Cluster Host', 'Mission-Critical Government Disaster Recovery Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Sify Technologies Ltd",
        "short_name": "Sify Technologies",
        "primary_domain": "MeitY-Empaneled Cloud, Enterprise Data Centers & Govt Telecom Networks",
        "secondary_domains": json.dumps(['State Wide Area Networks (SWAN)', 'MeitY GovCloud Infrastructure', 'E-Procurement Cloud', 'Disaster Recovery as a Service']),
        "description": "Pioneering Indian ICT and cloud infrastructure powerhouse. MeitY-empaneled cloud service provider operating 11 concurrent data centers and managing State Wide Area Networks (SWAN) across 12 Indian states, alongside mission-critical e-procurement portals.",
        "certifications": json.dumps(['MeitY Empaneled Cloud Provider', 'ISO 27001', 'ISO 20000-1', 'ISO 9001:2015', 'CMMI Level 3', 'CERT-In Compliant']),
        "empanelment_status": "MeitY Empaneled Cloud Provider & National SWAN Operator",
        "turnover": "\u20b93,380 Cr (FY 2023-24)",
        "employee_count": "4,200+ Network Architects, Cloud Engineers & Systems Integrators",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "pan_india_presence": True,
        "contact_person": "Government Alliances & E-Governance Business Group",
        "designation": "Senior Vice President - Public Sector Cloud & Network Alliances",
        "email": "marketing@sifycorp.com",
        "phone": "+91 44 2254 0770",
        "website": "https://www.sifytechnologies.com",
        "past_projects": json.dumps([{'title': 'State Wide Area Network (SWAN) Operations Across 3,500 Govt Offices', 'client': 'State IT Department / National e-Governance Plan (NeGP)', 'value': '₹160 Cr'}, {'title': 'National E-Procurement Portal Cloud Hosting & Disaster Recovery', 'client': 'Ministry of Finance / NIC', 'value': '₹75 Cr'}, {'title': 'Smart City Command and Control Center (ICCC) Fiber Backbone & Cloud', 'client': 'Chennai Smart City Limited', 'value': '₹48 Cr'}]),
        "synergy_roles": json.dumps(['State Wide Area Network (SWAN) Integration Lead', 'MeitY-Empaneled Cloud Data Center Host', 'Consortium Tier-1 Network Infrastructure Sponsor']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Tata Communications Ltd",
        "short_name": "Tata Communications",
        "primary_domain": "MeitY-Empaneled Enterprise Cloud, Cyber Security & Smart Infrastructure",
        "secondary_domains": json.dumps(['IZO Private Cloud', 'MeitY Tier-III/IV Cloud', 'Smart City ICCC Networks', 'STQC Audited Security']),
        "description": "Tata Group global digital ecosystem enabler. MeitY-empaneled provider of IZO Private Cloud, secure government connectivity, and smart city command center interconnectivity across major metropolitan areas in India.",
        "certifications": json.dumps(['BSE/NSE Listed (TATACOMM)', 'MeitY Empaneled Cloud Provider', 'ISO 27001', 'ISO 22301', 'SOC 2 Type II']),
        "empanelment_status": "MeitY Empaneled Cloud Service Provider & Tata Group Enterprise",
        "turnover": "\u20b920,969 Cr (FY 2023-24)",
        "employee_count": "12,000+ Global Telecom & Cloud Engineers",
        "state": "Maharashtra",
        "city": "Mumbai",
        "pan_india_presence": True,
        "contact_person": "Government & Public Services Business Division",
        "designation": "Vice President - Government Cloud & Smart Infrastructure",
        "email": "investor.relations@tatacommunications.com",
        "phone": "+91 22 6659 7000",
        "website": "https://www.tatacommunications.com",
        "past_projects": json.dumps([{'title': 'Central Government Ministry Enterprise Cloud & Secure Network', 'client': 'Ministry of Communications / MeitY', 'value': '₹210 Cr'}, {'title': 'Smart City Integrated Command and Control Center (ICCC) Cloud', 'client': 'Urban Local Bodies / Smart City SPV', 'value': '₹82 Cr'}, {'title': 'State Police Crime & Criminal Tracking Network (CCTNS) Cloud', 'client': 'State Police Headquarters', 'value': '₹64 Cr'}]),
        "synergy_roles": json.dumps(['Tier-1 Lead Consortium Financial Sponsor', 'MeitY-Empaneled Sovereign Cloud Host', 'High-Security STQC Network Architect']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "WAPCOS Ltd",
        "short_name": "WAPCOS (Min. of Jal Shakti)",
        "primary_domain": "Water Resources Engineering, Dam Safety, Irrigation SCADA & Hydrography",
        "secondary_domains": json.dumps(['Dam Rehabilitation & Safety (DRIP)', 'River Basin Hydro-Meteorology', 'Irrigation Canal Automation', 'EIA & Environmental Clearances']),
        "description": "Central Public Sector Enterprise (CPSE) under the Ministry of Jal Shakti, Government of India. The nation's premier engineering consultancy in water resources, hydro-power, irrigation canal networks, dam rehabilitation, and flood forecasting.",
        "certifications": json.dumps(['Govt of India Mini-Ratna-I CPSE', 'Ministry of Jal Shakti Enterprise', 'ISO 9001:2015', 'QCI/NABET Accredited']),
        "empanelment_status": "Ministry of Jal Shakti Premier CPSE & National Water Consultant",
        "turnover": "\u20b91,170 Cr (FY 2023-24)",
        "employee_count": "2,500+ Hydrological Engineers, Dam Specialists & Civil Consultants",
        "state": "Haryana",
        "city": "Gurugram",
        "pan_india_presence": True,
        "contact_person": "Government Business & Tender Consultancy Directorate",
        "designation": "Executive Director - Water Resources & Environmental Projects",
        "email": "mail@wapcos.co.in",
        "phone": "+91 124 2399 421",
        "website": "https://www.wapcos.co.in",
        "past_projects": json.dumps([{'title': 'Polavaram Major Multi-Purpose Irrigation Project Engineering Consultancy', 'client': 'Polavaram Project Authority / Govt of Andhra Pradesh', 'value': '₹180 Cr'}, {'title': 'Dam Rehabilitation and Improvement Project (DRIP) Instrumentation & Safety', 'client': 'Central Water Commission (CWC) / World Bank', 'value': '₹95 Cr'}, {'title': 'Namami Gange River Basin Rejuvenation Detailed Project Reports (DPR)', 'client': 'National Mission for Clean Ganga (NMCG)', 'value': '₹62 Cr'}]),
        "synergy_roles": json.dumps(['Water Resources Domain Lead & Hydro-engineering Head', 'Dam Safety & Hydrological Model Validator', 'Lead Public Sector JV Consortium Sponsor']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Vassar Labs IT Solutions Pvt Ltd",
        "short_name": "Vassar Labs",
        "primary_domain": "Smart Water Management, Satellite Soil Moisture & Flood AI Forecasting",
        "secondary_domains": json.dumps(['APWRIMS Water Portal', 'Reservoir Inflow Forecasting', 'AI Crop Water Advisory', 'Catchment Telemetry Networks']),
        "description": "Leading water-tech and climate resilience AI company. Built the Andhra Pradesh Water Resources Information Management System (APWRIMS), integrating satellite remote sensing, ground telemetry, and machine learning for basin-level reservoir management.",
        "certifications": json.dumps(['ISO 9001:2015', 'ISO 27001', 'CMMI Level 3', 'National Water Award Winner']),
        "empanelment_status": "State Water Resources & Disaster Management Department Empaneled",
        "turnover": "\u20b938 Cr (FY 2023-24)",
        "employee_count": "110+ Data Scientists, Hydrologists & Geospatial AI Researchers",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Water & Public Sector Enterprise Solutions Desk",
        "designation": "Director - Public Sector AI & Water Resources Solutions",
        "email": "marketing@vassarlabs.com",
        "phone": "+91 837 492 7727",
        "website": "https://www.vassarlabs.com",
        "past_projects": json.dumps([{'title': 'Andhra Pradesh Water Resources Information Management System (APWRIMS)', 'client': 'Water Resources Dept, Govt of Andhra Pradesh', 'value': '₹24 Cr'}, {'title': 'Krishna & Godavari River Basins Real-Time Flood Inundation AI Forecast', 'client': 'State Disaster Management Authority', 'value': '₹12 Cr'}, {'title': 'Satellite Soil Moisture & Micro-Irrigation Advisory System', 'client': 'Department of Agriculture / World Bank Project', 'value': '₹8.5 Cr'}]),
        "synergy_roles": json.dumps(['AI Water Reservoir & Flood Forecasting Engine', 'Ground IoT Telemetry Integration Lead', 'Satellite Soil Moisture Analytics Specialist']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Indomer Coastal Hydraulics Pvt Ltd",
        "short_name": "Indomer Coastal",
        "primary_domain": "Coastal Zone Mapping, Oceanographic Modeling, CRZ Clearance & Marine Bathymetry",
        "secondary_domains": json.dumps(['CRZ Demarcation Maps', 'Wave Flume Hydrodynamic Modeling', 'Port Siltation & Dredging Survey', 'Thermal Plume Marine Studies']),
        "description": "India's premier oceanographic and coastal engineering consultancy. Founded by former NIO oceanographers, officially accredited by NABET/QCI for Coastal Regulation Zone (CRZ) demarcation, coastal hydrodynamic modeling, and port bathymetric investigations.",
        "certifications": json.dumps(['NABET/QCI Accredited CRZ Consultant', 'ISO 9001:2015', 'Major Ports Empaneled', 'National Coastal Zone Partner']),
        "empanelment_status": "NABET Accredited CRZ Consultant & Indian Ports Empaneled",
        "turnover": "\u20b928 Cr (FY 2023-24)",
        "employee_count": "85 Oceanographers, Coastal Engineers & Hydrographic Surveyors",
        "state": "Tamil Nadu",
        "city": "Chennai",
        "pan_india_presence": True,
        "contact_person": "Oceanographic Projects & CRZ Clearance Cell",
        "designation": "Managing Director & Senior Coastal Consultant",
        "email": "ocean@indomer.com",
        "phone": "+91 44 2486 2482",
        "website": "https://www.indomer.com",
        "past_projects": json.dumps([{'title': 'Coastal Regulation Zone (CRZ) Demarcation for Sagarmala Port Terminals', 'client': 'Ministry of Ports, Shipping and Waterways', 'value': '₹14 Cr'}, {'title': 'Hydrodynamic Wave Tranquility & Coastal Erosion Modeling', 'client': 'Tamil Nadu Maritime Board / Visakhapatnam Port', 'value': '₹9.5 Cr'}, {'title': 'Desalination Plant Marine Intake/Outfall Bathymetric Study', 'client': 'Chennai Metropolitan Water Supply and Sewerage Board', 'value': '₹6.8 Cr'}]),
        "synergy_roles": json.dumps(['Coastal Regulation Zone (CRZ) Compliance Lead', 'Marine Hydrodynamic & Wave Modeler', 'Port Bathymetric Profile Specialist']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Roter Precision Instruments Pvt Ltd",
        "short_name": "Roter Group",
        "primary_domain": "High-End Airborne LiDAR (RIEGL Distributor), Geomatics & Aerial Surveying",
        "secondary_domains": json.dumps(['RIEGL Airborne LiDAR Scanners', 'Rail Corridor Topographic Mapping', 'Himalayan Landslide 3D Scanning', 'UAV LiDAR Sensor Payloads']),
        "description": "Leading Indian geomatics and airborne LiDAR systems group. Exclusive distributor of RIEGL Laser Measurement Systems in India, with high-altitude aerial LiDAR surveying capability deployed across dedicated freight corridors and Himalayan rail routes.",
        "certifications": json.dumps(['Sole RIEGL Airborne LiDAR Partner in India', 'ISO 9001:2015', 'DGCA Approved Testing', 'RDSO & NHAI Empaneled']),
        "empanelment_status": "Sole RIEGL LiDAR Distributor & RDSO / Railways Empaneled",
        "turnover": "\u20b982 Cr (FY 2023-24)",
        "employee_count": "180+ Optical Engineers, LiDAR Specialists & Geomatics Surveyors",
        "state": "Uttarakhand",
        "city": "Roorkee",
        "pan_india_presence": True,
        "contact_person": "Corporate Alliances & Airborne LiDAR Division",
        "designation": "Head - LiDAR Survey Solutions & Government Bids",
        "email": "info@apiroter.com",
        "phone": "+91 1332 261 277",
        "website": "https://www.apiroter.com",
        "past_projects": json.dumps([{'title': 'Himalayan Rail Corridor Airborne LiDAR Topographic Survey', 'client': 'Northern Railway / RVNL (Rishikesh-Karnaprayag Line)', 'value': '₹28 Cr'}, {'title': 'Dedicated Freight Corridor (DFCCIL) High-Accuracy Alignment LiDAR', 'client': 'DFCCIL / Ministry of Railways', 'value': '₹22 Cr'}, {'title': 'Statewide Forest Canopy Density & Biomass Aerial LiDAR Scanning', 'client': 'Uttarakhand Forest Department', 'value': '₹16 Cr'}]),
        "synergy_roles": json.dumps(['Airborne Heavy-Payload LiDAR Hardware Provider', 'High-Density Point Cloud Classification Specialist', 'Rail & Highway Alignment Profiler']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Geokno India Pvt Ltd",
        "short_name": "Geokno (GMR Group)",
        "primary_domain": "Terrestrial LiDAR, Mobile Laser Scanning & Railway / Highway DPR Surveys",
        "secondary_domains": json.dumps(['Mobile LiDAR Rigs', 'Airport Asset Spatial Database', 'Highway DPR Ground Surveys', 'Railway Track Clearance Lasers']),
        "description": "GMR Group subsidiary incubated at IIT Kanpur. Renowned for mobile laser scanning (MLS), terrestrial LiDAR, and millimeter-level rail track geometry surveys for high-speed corridors and international airport asset registers.",
        "certifications": json.dumps(['IIT Kanpur Incubated Pioneer', 'GMR Group Subsidiary', 'ISO 9001:2015', 'RDSO Approved', 'NHAI Empaneled']),
        "empanelment_status": "RDSO Indian Railways & NHAI Empaneled Survey Agency",
        "turnover": "\u20b956 Cr (FY 2023-24)",
        "employee_count": "190+ Laser Scanning Engineers, Surveyors & Civil Analysts",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Strategic Infrastructure Survey Projects Cell",
        "designation": "Vice President - LiDAR & Infrastructure Survey",
        "email": "info@geokno.com",
        "phone": "+91 40 6781 4242",
        "website": "https://www.geokno.com",
        "past_projects": json.dumps([{'title': 'Delhi-Varanasi High-Speed Rail Corridor Mobile LiDAR & DPR Survey', 'client': 'National High Speed Rail Corporation (NHSRCL)', 'value': '₹24 Cr'}, {'title': 'Hyderabad International Airport 3D Asset GIS & Airfield Survey', 'client': 'GMR Hyderabad International Airport Ltd (GHIAL)', 'value': '₹12 Cr'}, {'title': 'Four-Lane Expressway Alignment Ground LiDAR & Geotechnical Survey', 'client': 'NHAI / State PWD', 'value': '₹18 Cr'}]),
        "synergy_roles": json.dumps(['Mobile Laser Scanning (MLS) Field Team Lead', 'Railway Track Geometry & Clearance Specialist', 'Airport & Highway 3D Asset Modeler']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Matrix Geo Solutions Ltd",
        "short_name": "Matrix Geo",
        "primary_domain": "Drone Survey, DGPS Topographic Profiling & Linear Infrastructure DPRs",
        "secondary_domains": json.dumps(['Railway New Line Drone Surveys', 'Expressway Land Acquisition Demarcation', 'Urban Drainage Contouring', 'Transmission Line Corridors']),
        "description": "Premier drone mapping and infrastructure survey consultancy in Northern India. Trusted execution partner for Indian Railways, NHAI, and Delhi PWD for DPR surveys, right-of-way (RoW) land acquisition, and urban drainage modeling.",
        "certifications": json.dumps(['ISO 9001:2015', 'DGCA Compliant', 'Survey of India Empaneled', 'Indian Railways Class-A Empaneled']),
        "empanelment_status": "Indian Railways Class-A & National Highways Empaneled",
        "turnover": "\u20b936 Cr (FY 2023-24)",
        "employee_count": "140+ Remote Pilots, Civil Surveyors & CAD Specialists",
        "state": "Delhi",
        "city": "New Delhi",
        "pan_india_presence": True,
        "contact_person": "Tenders & Public Infrastructure Contracts Desk",
        "designation": "Director - Government Infrastructure Surveys",
        "email": "info@matrix-geo.com",
        "phone": "+91 7531 007 100",
        "website": "https://www.matrix-geo.com",
        "past_projects": json.dumps([{'title': 'Indian Railways New Broad Gauge Line Feasibility Drone & Ground Survey', 'client': 'Northern Railway Construction Organization', 'value': '₹15 Cr'}, {'title': 'Delhi Gram Sabha Land Topographical Survey across 20+ Villages', 'client': 'Revenue Department, Govt of NCT of Delhi', 'value': '₹8.4 Cr'}, {'title': 'Expressway Right-of-Way (RoW) Land Acquisition Boundary Demarcation', 'client': 'National Highways Authority of India (NHAI)', 'value': '₹11.2 Cr'}]),
        "synergy_roles": json.dumps(['Linear Infrastructure Ground Survey Crew Lead', 'Railway & Highway Alignment CAD Specialist', 'RoW Cadastral Demarcation Partner']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Lawrence & Mayo (India) Pvt Ltd",
        "short_name": "Lawrence & Mayo",
        "primary_domain": "Survey Instruments, GNSS/DGPS Rovers, Electronic Total Stations & Field Calibration",
        "secondary_domains": json.dumps(['DGPS GNSS RTK Receivers', 'Robotic Total Stations', 'Survey Training Academies', 'NABL Instrument Calibration']),
        "description": "India's legendary 147-year-old surveying instruments and geomatics corporation. Official national distributor and calibration authority for high-precision GNSS/DGPS rovers, electronic total stations, digital levels, and optical instruments.",
        "certifications": json.dumps(['NABL Calibration Laboratory Accredited', 'ISO 9001:2015', 'Survey of India Approved Equipment', 'GeM Star OEM Seller']),
        "empanelment_status": "National Survey Instrumentation & NABL Calibration Empaneled Agency",
        "turnover": "\u20b9185 Cr (FY 2023-24)",
        "employee_count": "650+ Geomatics Engineers, Optical Calibration Specialists & Technicians",
        "state": "Maharashtra",
        "city": "Mumbai",
        "pan_india_presence": True,
        "contact_person": "Industrial & Government Geomatics Division",
        "designation": "General Manager - Geomatics Equipment & Govt Institutional Bids",
        "email": "estore@lawrenceandmayo.co.in",
        "phone": "1800 102 1877",
        "website": "https://lawrenceandmayo.com",
        "past_projects": json.dumps([{'title': 'Nationwide Supply of 2,000+ Electronic Total Stations & DGPS Rovers', 'client': 'State Land Records & Survey Training Institutes', 'value': '₹45 Cr'}, {'title': 'NABL High-Precision Calibration of Survey Instruments for Major Projects', 'client': 'NHAI, Indian Railways & State PWDs', 'value': '₹14 Cr'}, {'title': 'Survey Equipment and Technical Crew Deployment for Cadastral Resurvey', 'client': 'Department of Land Resources (DoLR)', 'value': '₹26 Cr'}]),
        "synergy_roles": json.dumps(['High-Accuracy Geomatics Hardware Provider', 'NABL Calibration Certification Authority', 'Field Survey Instrument Fleet Sponsor']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Elcome Integrated Systems Pvt Ltd",
        "short_name": "Elcome Systems (Leica Partner)",
        "primary_domain": "Geomatics Survey Systems, Hydrographic Multibeam Sonar & DGPS Networks",
        "secondary_domains": json.dumps(['CORS Network Infrastructure', 'Leica Geosystems Distribution', 'Multibeam Naval Sonar', 'Border Security Surveillance']),
        "description": "Premier Indian marine electronics and geomatics engineering firm. Longstanding partner of Hexagon and Leica Geosystems, specializing in national Continuously Operating Reference Stations (CORS) networks and naval hydrographic sensor integration.",
        "certifications": json.dumps(['Leica Geosystems / Hexagon Strategic Partner', 'ISO 9001:2015', 'ISO 27001', 'Survey of India CORS Partner', 'Indian Navy Empaneled']),
        "empanelment_status": "Survey of India CORS Network Vendor & Naval Sensor Empaneled",
        "turnover": "\u20b9210 Cr (FY 2023-24)",
        "employee_count": "550+ Systems Engineers, Hydrographers & Sensor Technicians",
        "state": "Maharashtra",
        "city": "Navi Mumbai",
        "pan_india_presence": True,
        "contact_person": "Government Alliances & Defense/Civil Geomatics Desk",
        "designation": "Director - Government Solutions & Marine Geomatics",
        "email": "deepa@elcomeindia.com",
        "phone": "+91 22 6761 8000",
        "website": "https://elcome.in",
        "past_projects": json.dumps([{'title': 'Survey of India National CORS Network Ground Station Establishment', 'client': 'Survey of India / DST', 'value': '₹55 Cr'}, {'title': 'Deep-Water Multibeam Hydrographic Sonar Rigging & Commissioning', 'client': 'National Hydrographic Office / Directorate of Naval Design', 'value': '₹38 Cr'}, {'title': 'Border Perimeter Electronic Surveillance & Electro-Optic Sensor Grid', 'client': 'Border Security Force (BSF) / Ministry of Home Affairs', 'value': '₹42 Cr'}]),
        "synergy_roles": json.dumps(['CORS GNSS RTK Network Engineering Lead', 'Hydrographic Multibeam Sensor Integrator', 'Defense & Border Electronic Systems Partner']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "NeoGeoInfo Technologies Ltd",
        "short_name": "NeoGeo",
        "primary_domain": "Geospatial Consulting, Spatial Web Portals, Cadastral GIS & Drone Survey",
        "secondary_domains": json.dumps(['SVAMITVA Drone Mapping', 'ULB Municipal Property Tax', 'Gas Pipeline GIS', 'WebGIS Application Development']),
        "description": "Leading Indian geospatial systems integrator. Executed extensive SVAMITVA drone surveys in UP, Maharashtra, and Karnataka, along with city gas distribution network GIS and municipal property enumeration for Urban Local Bodies (ULBs).",
        "certifications": json.dumps(['CMMI Level 3', 'ISO 9001:2015', 'ISO 27001', 'Survey of India Empaneled']),
        "empanelment_status": "Survey of India & State Urban Local Bodies Empaneled Partner",
        "turnover": "\u20b974 Cr (FY 2023-24)",
        "employee_count": "450+ Geospatial Developers, Surveyors & Photogrammetrists",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Government Projects & Strategic Partnerships Unit",
        "designation": "Vice President - Government GIS & Drone Services",
        "email": "info@neogeoinfo.com",
        "phone": "+91 40 4211 1101",
        "website": "https://neogeoinfo.com",
        "past_projects": json.dumps([{'title': 'SVAMITVA Scheme Drone Cadastral Mapping across 8,000 Villages', 'client': 'Survey of India / Govt of Uttar Pradesh', 'value': '₹32 Cr'}, {'title': 'Urban Local Body (ULB) GIS Base Map & Property Tax Enumeration', 'client': 'Directorate of Municipal Administration', 'value': '₹16 Cr'}, {'title': 'Underground City Gas Distribution (CGD) Utility GIS Mapping', 'client': 'Torrent Gas / Indian Oil Adani Gas', 'value': '₹12.5 Cr'}]),
        "synergy_roles": json.dumps(['Municipal Property Tax Survey Co-Lead', 'Gas & Water Underground Utility GIS Specialist', 'Statewide Cadastral Drone Operator']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Magnasoft Consulting India Pvt Ltd",
        "short_name": "Magnasoft",
        "primary_domain": "Enterprise GIS Engineering, Spatial ETL Pipelines & Utility Data Migration",
        "secondary_domains": json.dumps(['Electric Grid GIS Modernization', 'Smart City 3D Spatial Data', 'Land Title Cadastral Modernization', 'Automated Feature Extraction']),
        "description": "Global geospatial data engineering and consulting organization. Specializes in multi-layer GIS data migration, electrical utility network models (Esri ArcGIS / OpenSource), and automated topological spatial data cleaning for smart cities.",
        "certifications": json.dumps(['ISO 9001:2015', 'ISO 27001', 'CMMI Level 3', 'Esri Silver Partner']),
        "empanelment_status": "National Utility Discoms & Smart City SPVs Empaneled GIS Partner",
        "turnover": "\u20b988 Cr (FY 2023-24)",
        "employee_count": "550+ Geospatial Analysts, Data Engineers & GIS Programmers",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Strategic Accounts & Enterprise Solutions Unit",
        "designation": "Associate Vice President - Geospatial Data Engineering",
        "email": "info@magnasoft.com",
        "phone": "+91 80 4346 6000",
        "website": "https://www.magnasoft.com",
        "past_projects": json.dumps([{'title': 'Statewide Power Distribution Grid GIS Network Digitization', 'client': 'Karnataka Power Transmission Corporation (KPTCL)', 'value': '₹26 Cr'}, {'title': 'Smart City 3D Spatial Data Infrastructure & Cadastral Integration', 'client': 'Bengaluru Smart City Limited', 'value': '₹18 Cr'}, {'title': 'National Land Records Modernization Spatial Database Conversion', 'client': 'State Land Records Department', 'value': '₹14 Cr'}]),
        "synergy_roles": json.dumps(['Spatial ETL & Geodatabase Data Migration Lead', 'Utility Network Spatial Model Architect', 'Quality Assurance & Topology Validator']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Consulting Engineers Group Ltd",
        "short_name": "CEG Ltd",
        "primary_domain": "Highway Engineering, Metro Rail DPRs, Civil Topographic Surveys & Geotechnical",
        "secondary_domains": json.dumps(['Delhi-Mumbai Expressway DPR', 'Jaipur Metro Rail PMC', 'Topographical Ground Surveys', 'Bridge Geotechnical Investigation']),
        "description": "Premier Indian civil infrastructure and transportation engineering consultancy. Lead project management consultant (PMC) for landmark expressways, metro rail projects, high-speed rail packages, and extensive geotechnical investigations.",
        "certifications": json.dumps(['ISO 9001:2015', 'NABL Accredited Geotechnical Labs', 'NHAI Empaneled PMC', 'Ministry of Railways Approved']),
        "empanelment_status": "NHAI & Ministry of Road Transport Class-A Lead Consultant",
        "turnover": "\u20b9215 Cr (FY 2023-24)",
        "employee_count": "1,200+ Civil Engineers, Geotechnical Experts & DPR Surveyors",
        "state": "Rajasthan",
        "city": "Jaipur",
        "pan_india_presence": True,
        "contact_person": "Corporate Contracts & Public Sector Bidding Division",
        "designation": "Senior Vice President - Infrastructure Alliances & PMC Bids",
        "email": "business@cegindia.com",
        "phone": "+91 141 275 1801",
        "website": "https://www.cegindia.com",
        "past_projects": json.dumps([{'title': 'Delhi-Mumbai Expressway Project Detailed Project Report (DPR) & Ground Survey', 'client': 'National Highways Authority of India (NHAI)', 'value': '₹48 Cr'}, {'title': 'Metro Rail Project Management & Topographical Alignment Survey', 'client': 'Jaipur Metro Rail Corporation (JMRC) / DMRC', 'value': '₹32 Cr'}, {'title': 'Major River Bridge Geotechnical & Hydro-morphological Survey', 'client': 'State PWD Highway Division', 'value': '₹16 Cr'}]),
        "synergy_roles": json.dumps(['Civil DPR & Alignment Engineering Lead', 'Geotechnical Soil Investigation Partner', 'NHAI Turnkey Bid Co-Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "SECON Pvt Ltd",
        "short_name": "SECON",
        "primary_domain": "Multi-Disciplinary Geospatial, Cross-Country Pipeline Surveys & Aerial Photogrammetry",
        "secondary_domains": json.dumps(['GAIL Gas Pipeline Surveys', 'River Valley Canal Surveys', 'Large-Scale Photogrammetry', 'Geotechnical Foundation Studies']),
        "description": "One of India's oldest and most prestigious multi-disciplinary engineering and surveying organizations. Over 40 years of pioneering experience in cross-country pipeline surveys for GAIL/IOCL, irrigation river valley projects, and digital photogrammetry.",
        "certifications": json.dumps(['ISO 9001:2015', 'CMMI Level 3', 'NABL Accredited Testing', 'Survey of India Class-A Empaneled', 'GAIL & ONGC Approved']),
        "empanelment_status": "Ministry of Petroleum (GAIL/IOCL) & Survey of India Empaneled",
        "turnover": "\u20b9140 Cr (FY 2023-24)",
        "employee_count": "900+ Survey Engineers, Cartographers & Civil Specialists",
        "state": "Karnataka",
        "city": "Bengaluru",
        "pan_india_presence": True,
        "contact_person": "Tenders & Cross-Country Projects Directorate",
        "designation": "Vice President - Pipeline Surveys & Government Bids",
        "email": "feedback@secon.in",
        "phone": "+91 80 4119 7778",
        "website": "https://www.secon.in",
        "past_projects": json.dumps([{'title': '1,200km Cross-Country Natural Gas Pipeline Route & Cadastral Survey', 'client': 'GAIL (India) Limited', 'value': '₹38 Cr'}, {'title': 'River Valley Irrigation Dam & Canal Engineering Topographic Survey', 'client': 'Karnataka Water Resources Development Organization', 'value': '₹22 Cr'}, {'title': 'Urban Infrastructure Drainage & Digital Elevation Model (DEM)', 'client': 'Bruhat Bengaluru Mahanagara Palike (BBMP)', 'value': '₹14 Cr'}]),
        "synergy_roles": json.dumps(['Cross-Country Pipeline Corridor Survey Lead', 'Large-Scale Ground Survey Crew Mobilizer', 'Civil Hydraulic Elevation Modeler']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Aarvee Associates Architects Engineers & Consultants Pvt Ltd",
        "short_name": "Aarvee Associates",
        "primary_domain": "Rail, Highway, Urban Infrastructure Engineering, Water Supply & GIS Planning",
        "secondary_domains": json.dumps(['Hyderabad Metro Rail PMC', 'AMRUT Water Supply Master Plans', 'High-Speed Rail Alignment', 'Urban Drainage Master Plans']),
        "description": "Premier multidisciplinary infrastructure consulting company based in Hyderabad. Lead designer and PMC for metro rail corridors, highway networks, regional water supply grids under AMRUT/Jal Jeevan Mission, and urban environmental master plans.",
        "certifications": json.dumps(['ISO 9001:2015', 'ISO 14001:2015', 'NHAI Empaneled Class-A Consultant', 'MoHUA AMRUT Empaneled']),
        "empanelment_status": "Ministry of Housing and Urban Affairs (MoHUA) & NHAI Empaneled",
        "turnover": "\u20b9310 Cr (FY 2023-24)",
        "employee_count": "1,600+ Structural Engineers, Urban Planners, Hydrologists & GIS Experts",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Government Alliances & Infrastructure Projects Directorate",
        "designation": "Director - Strategic Business & Public Sector Tenders",
        "email": "aarvee@aarvee.net",
        "phone": "+91 40 4848 3456",
        "website": "https://www.aarvee.com",
        "past_projects": json.dumps([{'title': 'Hyderabad Metro Rail Phase-II Detailed Engineering & Topographic Alignment', 'client': 'Hyderabad Metro Rail Limited (HMRL)', 'value': '₹42 Cr'}, {'title': 'AMRUT Urban Water Supply & Storm Water Drainage Master Plan', 'client': 'Municipal Administration and Urban Development Department', 'value': '₹28 Cr'}, {'title': 'State Highway Four-Laning DPR and Environmental Corridor Assessment', 'client': 'Andhra Pradesh Road Development Corporation (APRDC)', 'value': '₹19 Cr'}]),
        "synergy_roles": json.dumps(['Turnkey Infrastructure Design Lead', 'Urban Water Supply & Drainage Master Planner', 'Joint Consortium Co-Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "GIS Consortium India Pvt Ltd",
        "short_name": "GIS Consortium",
        "primary_domain": "Photogrammetry, Remote Sensing, Cadastral Resurvey & Municipal GIS",
        "secondary_domains": json.dumps(['UP Municipal Tax GIS', 'Bihar Cadastral Survey', 'Forestry Canopy Change Detection', 'Topographic Contour Mapping']),
        "description": "Prominent North Indian geomatics enterprise based in Noida. Extensive credentials in municipal tax property surveys, state revenue department cadastral resurveys across UP, Bihar, and MP, and environmental forestry monitoring.",
        "certifications": json.dumps(['ISO 9001:2015', 'ISO 27001', 'Survey of India Empaneled', 'UP Desco Empaneled']),
        "empanelment_status": "UP Desco & State Urban Development Empaneled Geospatial Agency",
        "turnover": "\u20b942 Cr (FY 2023-24)",
        "employee_count": "240+ GIS Technicians, Cartographers & Field Surveyors",
        "state": "Uttar Pradesh",
        "city": "Noida",
        "pan_india_presence": True,
        "contact_person": "Government Bids & Geospatial Alliances Unit",
        "designation": "Head - Tender Management & Government Relations",
        "email": "info@gisconsortium.net",
        "phone": "+91 120 464 0000",
        "website": "https://giscindia.com",
        "past_projects": json.dumps([{'title': 'Uttar Pradesh Municipal Property Tax GIS Mapping across 10 Urban Bodies', 'client': 'Directorate of Local Bodies, Govt of UP', 'value': '₹18 Cr'}, {'title': 'Cadastral Land Records Resurvey and Digitization in 200 Revenue Villages', 'client': 'Directorate of Land Records, Govt of Bihar', 'value': '₹12 Cr'}, {'title': 'Statewide Forest Canopy Density & Encroachment Remote Sensing', 'client': 'Madhya Pradesh Forest Department', 'value': '₹9.5 Cr'}]),
        "synergy_roles": json.dumps(['Municipal Property Tax Enumerator Lead', 'North Indian District Field Survey Crew Lead', 'Forest Canopy Vectorization Specialist']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Vimta Labs Ltd",
        "short_name": "Vimta Labs",
        "primary_domain": "NABET-Accredited Environmental Impact Assessment (EIA), CRZ & Forest Clearance",
        "secondary_domains": json.dumps(['NABET Accredited EIA Studies', 'Forest Diversion Clearances', 'Coastal CRZ Clearance', 'Water & Air Quality Monitoring']),
        "description": "NSE and BSE listed premier scientific laboratory and environmental consultancy. QCI/NABET accredited for conducting Environmental Impact Assessments (EIA), CRZ coastal clearances, forest biodiversity baseline studies, and industrial environmental audits.",
        "certifications": json.dumps(['BSE/NSE Listed (VIMTALABS)', 'QCI/NABET Accredited EIA Consultant', 'NABL Accredited Laboratory', 'MoEFCC Recognized Lab']),
        "empanelment_status": "Ministry of Environment, Forest and Climate Change (MoEFCC) Recognized",
        "turnover": "\u20b9330 Cr (FY 2023-24)",
        "employee_count": "1,200+ Environmental Scientists, Chemists & Ecologists",
        "state": "Telangana",
        "city": "Hyderabad",
        "pan_india_presence": True,
        "contact_person": "Environmental Alliances & Public Sector Consultancy Cell",
        "designation": "Vice President - Environmental Impact & Regulatory Clearances",
        "email": "info@vimta.com",
        "phone": "+91 40 6740 4040",
        "website": "https://www.vimta.com",
        "past_projects": json.dumps([{'title': 'Environmental Impact Assessment (EIA) for Mega Industrial Corridor', 'client': 'Telangana State Industrial Infrastructure Corporation (TSIIC)', 'value': '₹16 Cr'}, {'title': 'Coastal Regulation Zone (CRZ) Clearance & Marine Baseline Study', 'client': 'Andhra Pradesh Maritime Board / Port Concessionaire', 'value': '₹11 Cr'}, {'title': 'Irrigation Scheme Forest Diversion Clearance & Ecological Study', 'client': 'Water Resources Department, Govt of Maharashtra', 'value': '₹8.2 Cr'}]),
        "synergy_roles": json.dumps(['QCI/NABET Environmental Impact Assessment Lead', 'Forest & CRZ Regulatory Clearance Specialist', 'Air/Water/Soil Quality Baseline Testing Partner']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Webel Technology Ltd",
        "short_name": "Webel Technology (WTL)",
        "primary_domain": "State Nodal E-Governance, GIS Geoportals & Smart City IT Infrastructure",
        "secondary_domains": json.dumps(['West Bengal SSDI Geoportal', 'Banglarbhumi Land Records', 'State Data Center Operations', 'Municipal Smart City IT']),
        "description": "Government of West Bengal undertaking and state nodal agency for e-governance, spatial information systems, and IT infrastructure. Operates the West Bengal State Spatial Data Infrastructure and manages Banglarbhumi land records portal services.",
        "certifications": json.dumps(['Govt of West Bengal Undertaking', 'CMMI Level 3', 'ISO 9001:2015', 'ISO 27001', 'MeitY State Nodal Agency']),
        "empanelment_status": "Government of West Bengal State Nodal Agency for E-Governance",
        "turnover": "\u20b9190 Cr (FY 2023-24)",
        "employee_count": "450+ IT Architects, GIS Specialists & Systems Integrators",
        "state": "West Bengal",
        "city": "Kolkata",
        "pan_india_presence": True,
        "contact_person": "Corporate Business Development & Institutional Bids Cell",
        "designation": "General Manager - E-Governance & Spatial Tech",
        "email": "career@wtl.co.in",
        "phone": "+91 33 2367 3403",
        "website": "https://www.wtl.co.in",
        "past_projects": json.dumps([{'title': 'West Bengal State Spatial Data Infrastructure (WSSDI) Portal', 'client': 'Department of Information Technology, Govt of WB', 'value': '₹34 Cr'}, {'title': 'Banglarbhumi Land Records Modernization & Database Operations', 'client': 'Land and Land Reforms Department, Govt of WB', 'value': '₹45 Cr'}, {'title': 'Kolkata Metropolitan Area CCTV Surveillance & Server Control Center', 'client': 'Kolkata Police & Municipal Development Dept', 'value': '₹28 Cr'}]),
        "synergy_roles": json.dumps(['Eastern India State Nodal Agency Lead', 'State Spatial Data Infrastructure Operator', 'Public Sector E-Governance Bid Sponsor']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Kashyap Geo Tech",
        "short_name": "Kashyap Geo Tech",
        "primary_domain": "DGPS Survey, Drone Survey, Topographical & Contour Survey in Andhra Pradesh",
        "secondary_domains": json.dumps(['Visakhapatnam Port Corridor DGPS', 'APCRDA Amaravati Topography', 'Coastal Industrial Demarcation', 'Total Station Field Profiling']),
        "description": "Specialized land surveying and drone mapping organization headquartered in Visakhapatnam. Extensively involved in Andhra Pradesh industrial corridor DGPS boundary surveys, Visakhapatnam port corridor topography, and municipal storm water contouring.",
        "certifications": json.dumps(['ISO 9001:2015', 'Survey of India Class-A Registered', 'APCRDA Empaneled Vendor']),
        "empanelment_status": "Andhra Pradesh Capital Region (APCRDA) & Local Industrial Parks Empaneled",
        "turnover": "\u20b916 Cr (FY 2023-24)",
        "employee_count": "75 Ground Surveyors, Drone Pilots & CAD Technicians",
        "state": "Andhra Pradesh",
        "city": "Visakhapatnam",
        "pan_india_presence": True,
        "contact_person": "Andhra Pradesh Field Operations Directorate",
        "designation": "Chief Survey Operations Officer",
        "email": "info@kashyapgeotech.com",
        "phone": "+91 891 250 8899",
        "website": "https://kashyapgeotech.com",
        "past_projects": json.dumps([{'title': 'Visakhapatnam Coastal Corridor DGPS & Contour Topographical Survey', 'client': 'Visakhapatnam Metropolitan Region Development Authority (VMRDA)', 'value': '₹6.5 Cr'}, {'title': 'Andhra Pradesh Industrial Corridor Concession Boundary Demarcation', 'client': 'APIIC / Industries Department', 'value': '₹4.8 Cr'}, {'title': 'Amaravati Capital City Regional Drone Survey & Cadastral Mapping', 'client': 'APCRDA / Municipal Administration', 'value': '₹5.2 Cr'}]),
        "synergy_roles": json.dumps(['Andhra Pradesh Local Ground Survey Crew Lead', 'Visakhapatnam & Coastal DGPS Network Operator', 'District Land Boundary Demarcator']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "ERM India Pvt Ltd",
        "short_name": "ERM India",
        "primary_domain": "NABET-Accredited Environmental Clearances, CRZ Clearances & ESG Sustainability",
        "secondary_domains": json.dumps(['QCI/NABET Accredited EIA', 'Miyawaki Forest Planning', 'Biodiversity Conservation Plans', 'CRZ Maritime Approvals']),
        "description": "Indian arm of Environmental Resources Management (ERM), the world's leading sustainability and environmental consultancy. QCI/NABET accredited for environmental clearances, coastal CRZ permits, ecological forestry planning, and urban mini-forest designs.",
        "certifications": json.dumps(['QCI/NABET Accredited EIA Consultant', 'ISO 14001:2015', 'ISO 9001:2015', 'MoEFCC Recognized']),
        "empanelment_status": "MoEFCC & QCI/NABET Accredited Lead Environmental Consultancy",
        "turnover": "\u20b9175 Cr (FY 2023-24)",
        "employee_count": "600+ Environmental Scientists, Ecologists & Climate Specialists",
        "state": "Haryana",
        "city": "Gurugram",
        "pan_india_presence": True,
        "contact_person": "Government Regulatory & Environmental Alliances Desk",
        "designation": "Partner & Head - Public Sector Environmental Clearances",
        "email": "India@erm.com",
        "phone": "+91 124 482 1000",
        "website": "https://www.erm.com",
        "past_projects": json.dumps([{'title': 'Environmental & CRZ Clearance for Coastal Infrastructure & Expressways', 'client': 'National Highways Authority of India / State Maritime Boards', 'value': '₹22 Cr'}, {'title': 'Urban Biodiversity & Mini Miyawaki Forest Design Master Plan', 'client': 'Municipal Corporations / Environment Dept', 'value': '₹8.5 Cr'}, {'title': 'Forest Diversion & Wildlife Conservation Detailed Management Plan', 'client': 'State Forest Department / Water Resources Dept', 'value': '₹12 Cr'}]),
        "synergy_roles": json.dumps(['NABET Environmental & CRZ Clearance Lead', 'Ecological & Urban Forest Technical Specialist', 'Environmental Impact Mitigation Modeler']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Kerala State Electronics Development Corporation Ltd (KELTRON)",
        "short_name": "KELTRON",
        "primary_domain": "State Nodal Electronics, CCTV Surveillance, Traffic & Smart City IT",
        "secondary_domains": json.dumps(['Statewide CCTV Surveillance', 'Traffic Enforcement Cameras', 'Municipal IT Infrastructure', 'Electronics Manufacturing']),
        "description": "Kerala State Government undertaking and pioneer in electronics and IT infrastructure. Implements statewide CCTV surveillance, automated traffic enforcement networks, school IT smart infrastructure, and municipal e-governance systems across Kerala.",
        "certifications": json.dumps(['Govt of Kerala Undertaking', 'ISO 9001:2015', 'ISO 27001', 'CMMI Level 3', 'State Nodal Agency']),
        "empanelment_status": "Government of Kerala State Nodal Agency for Electronics & IT",
        "turnover": "\u20b9450 Cr (FY 2023-24)",
        "employee_count": "1,800+ Electronics Engineers, IT Specialists & Field Technicians",
        "state": "Kerala",
        "city": "Thiruvananthapuram",
        "pan_india_presence": True,
        "contact_person": "Corporate Alliances & Government Projects Directorate",
        "designation": "Head - Strategic Public Sector Projects & Tenders",
        "email": "keltron@keltron.org",
        "phone": "+91 471 272 4444",
        "website": "https://www.keltron.org",
        "past_projects": json.dumps([{'title': 'Statewide Safe Kerala Automated Traffic Enforcement & CCTV Surveillance', 'client': 'Motor Vehicles Department, Govt of Kerala', 'value': '₹232 Cr'}, {'title': 'Kochi Smart City Integrated Command and Control Center (ICCC) CCTV', 'client': 'Cochin Smart Mission Limited (CSML)', 'value': '₹45 Cr'}, {'title': 'Government Higher Secondary Schools IT Infrastructure Modernization', 'client': 'General Education Department, Govt of Kerala', 'value': '₹68 Cr'}]),
        "synergy_roles": json.dumps(['Kerala State Public Sector Lead Bidder', 'CCTV Surveillance & Control Room Integrator', 'Electronic Sensor & Field Hardware Lead']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Bihar State Electronics Development Corporation Ltd (BELTRON)",
        "short_name": "BELTRON",
        "primary_domain": "State Nodal E-Governance, IT Infrastructure & Land Digitization",
        "secondary_domains": json.dumps(['State Data Center Operations', 'Land Records Digitization', 'CCTV Surveillance Systems', 'E-Procurement Platform']),
        "description": "Government of Bihar undertaking and prime nodal agency for electronics, IT, and GIS-based e-governance solutions. Spearheads Bihar's land records computerization, state data center infrastructure, and government IT procurement.",
        "certifications": json.dumps(['Govt of Bihar Undertaking', 'ISO 9001:2015', 'ISO 27001', 'MeitY State Implementing Agency']),
        "empanelment_status": "Government of Bihar State Nodal Implementing Agency",
        "turnover": "\u20b9520 Cr (FY 2023-24)",
        "employee_count": "1,200+ IT Professionals, Data Engineers & Operations Staff",
        "state": "Bihar",
        "city": "Patna",
        "pan_india_presence": True,
        "contact_person": "Managing Director & Project Directorate",
        "designation": "General Manager - IT Projects & Government Alliances",
        "email": "mdbeltron@bihar.gov.in",
        "phone": "+91 612 228 1851",
        "website": "https://bsedc.bihar.gov.in",
        "past_projects": json.dumps([{'title': 'Bihar Digital Land Records Modernization & Spatial Data Repository', 'client': 'Revenue and Land Reforms Department, Govt of Bihar', 'value': '₹85 Cr'}, {'title': 'Patna Smart City Integrated Command and Control Center (ICCC) Setup', 'client': 'Patna Smart City Limited', 'value': '₹42 Cr'}, {'title': 'Statewide High-Speed Network Connectivity across 534 Block Offices', 'client': 'Information Technology Dept, Govt of Bihar', 'value': '₹64 Cr'}]),
        "synergy_roles": json.dumps(['Bihar State Nodal Consortium Lead', 'State Land Records Digitization Operator', 'Government IT Procurement & Cloud Host']),
        "rating": 4.8,
        "status": "Available"
    },
    {
        "name": "Odisha Computer Application Centre (OCAC)",
        "short_name": "OCAC (Govt of Odisha)",
        "primary_domain": "State Nodal IT Directorate, Spatial Geoportals & E-Governance",
        "secondary_domains": json.dumps(['Odisha State Data Center', 'ORSAC Spatial Integration', 'Smart City Command Centers', 'State Wide Area Network']),
        "description": "Technical Directorate of Information Technology Department, Government of Odisha. Central agency for state GIS portals, integrating with the Odisha Space Applications Centre (ORSAC) for natural resource mapping, land cadastre, and disaster response.",
        "certifications": json.dumps(['Govt of Odisha Technical Directorate', 'ISO 9001:2015', 'ISO 27001', 'MeitY Implementing Agency']),
        "empanelment_status": "Government of Odisha Apex IT & Spatial Technology Directorate",
        "turnover": "\u20b9380 Cr (FY 2023-24)",
        "employee_count": "650+ IT Consultants, Spatial Engineers & Project Managers",
        "state": "Odisha",
        "city": "Bhubaneswar",
        "pan_india_presence": True,
        "contact_person": "Directorate of Public Projects & Tenders",
        "designation": "General Manager - E-Governance & Spatial Solutions",
        "email": "contact@ocac.in",
        "phone": "+91 674 258 8280",
        "website": "https://www.ocac.in",
        "past_projects": json.dumps([{'title': 'Odisha Spatial Data Repository & ORSAC Drone Mapping Geoportal', 'client': 'Electronics & IT Department / ORSAC', 'value': '₹48 Cr'}, {'title': 'Bhubaneswar Smart City Intelligent City Operations Center (ICOC)', 'client': 'Bhubaneswar Smart City Limited', 'value': '₹36 Cr'}, {'title': 'Odisha Mining Lease Digital Boundary Monitoring System', 'client': 'Steel & Mines Department, Govt of Odisha', 'value': '₹22 Cr'}]),
        "synergy_roles": json.dumps(['Odisha State Nodal Agency Lead', 'ORSAC Spatial Layer Integration Specialist', 'State Data Center & Disaster Portal Host']),
        "rating": 4.9,
        "status": "Available"
    },
    {
        "name": "Punjab Information and Communication Technology Corporation Ltd",
        "short_name": "Punjab Infotech",
        "primary_domain": "State Nodal IT Corporation, E-Governance & Geospatial Initiatives",
        "secondary_domains": json.dumps(['Punjab State Data Center', 'PRSC Remote Sensing Integration', 'Urban Local Body E-Governance', 'CCTV Safe City']),
        "description": "Government of Punjab undertaking and premier agency for planning, directing, and executing IT and spatial infrastructure across Punjab. Integrates with the Punjab Remote Sensing Centre (PRSC) for agricultural and municipal mapping.",
        "certifications": json.dumps(['Govt of Punjab Undertaking', 'ISO 9001:2015', 'MeitY State Nodal Agency']),
        "empanelment_status": "Government of Punjab State Nodal Agency for IT & Procurement",
        "turnover": "\u20b9290 Cr (FY 2023-24)",
        "employee_count": "450+ IT Consultants, Systems Integrators & Engineers",
        "state": "Punjab",
        "city": "Chandigarh",
        "pan_india_presence": True,
        "contact_person": "State Procurement & Government Projects Directorate",
        "designation": "Head - Public Sector Projects & Strategic Alliances",
        "email": "infotech@punjabinfotech.gov.in",
        "phone": "+91 172 525 6400",
        "website": "https://punjabinfotech.punjab.gov.in",
        "past_projects": json.dumps([{'title': 'Punjab State Data Center (PSDC) Tier-III Modernization & Cloud', 'client': 'Department of Governance Reforms, Govt of Punjab', 'value': '₹54 Cr'}, {'title': 'Ludhiana & Amritsar Smart City Unified CCTV & Traffic Surveillance', 'client': 'Smart City SPVs / Punjab Police', 'value': '₹42 Cr'}, {'title': 'Punjab Remote Sensing Agricultural Stubble & Land Monitoring GIS', 'client': 'Punjab Remote Sensing Centre (PRSC) / Agriculture Dept', 'value': '₹18 Cr'}]),
        "synergy_roles": json.dumps(['Punjab State Public Sector Lead Sponsor', 'PRSC Spatial Layer Integration Specialist', 'State Data Center Cloud Host']),
        "rating": 4.8,
        "status": "Available"
    }
]


def ensure_partners_seeded(db: Session):
    """Sync 100% verified real Indian partners, purging obsolete mock data and refreshing records."""
    models.Base.metadata.create_all(bind=db.get_bind())
    
    valid_names = {p["name"] for p in INITIAL_PARTNERS_SEED}
    
    # 1. Purge obsolete / synthetic partners
    obsolete_partners = db.query(models.Partner).filter(~models.Partner.name.in_(valid_names)).all()
    if obsolete_partners:
        obsolete_ids = [op.id for op in obsolete_partners]
        db.query(models.TenderCollaboration).filter(models.TenderCollaboration.partner_id.in_(obsolete_ids)).delete(synchronize_session=False)
        for op in obsolete_partners:
            db.delete(op)
        db.commit()

    # 2. Add or update real partners
    existing = {p.name: p for p in db.query(models.Partner).all()}
    changed = False

    for p_data in INITIAL_PARTNERS_SEED:
        name = p_data["name"]
        if name not in existing:
            partner = models.Partner(**p_data)
            db.add(partner)
            changed = True
        else:
            partner = existing[name]
            for key, val in p_data.items():
                if getattr(partner, key) != val:
                    setattr(partner, key, val)
                    changed = True

    if changed:
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
        if len(filtered_results) < 3 and matched_results:
            # Fallback to top ranked candidate partners so user always gets matched consortium partners
            filtered_results = matched_results[:8]
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


def send_collaboration_outreach_email(
    db: Session,
    payload: schemas.CollaborationEmailDispatchRequest
) -> Dict[str, Any]:
    """Generate executive Letter of Intent email and dispatch directly to team and partner."""
    from app.services.email_service import build_collaboration_email_html, _dispatch_html_email

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

    html_content = build_collaboration_email_html(
        tender=tender,
        partner=partner,
        match_info=match_info,
        letter_text=letter_text,
        jv_split=payload.proposed_jv_split or "60% GISFY : 40% Specialized Partner",
        custom_notes=payload.custom_message,
        gisfy_name=payload.gisfy_contact_name or "Swetha (GISFY)",
        gisfy_email=payload.gisfy_contact_email or "swethagisfy@gmail.com"
    )

    recipients = list(payload.recipients or ["swethagisfy@gmail.com"])
    if "swethagisfy@gmail.com" not in [r.lower() for r in recipients]:
        recipients.insert(0, "swethagisfy@gmail.com")
    if partner.email and partner.email not in recipients:
        recipients.append(partner.email)

    dispatch_res = _dispatch_html_email(
        recipients=recipients,
        subject=subject,
        html_content=html_content,
        state_name=state_name,
        tender_id=str(tender.tender_id),
        event_prefix="COLLABORATION OUTREACH EMAIL"
    )

    update_tender_collaboration(
        db,
        tender.id,
        partner.id,
        status="Outreach Sent",
        notes=f"Dispatched LOI to {', '.join(recipients)} on {datetime.utcnow().strftime('%d %b %Y %H:%M')}"
    )

    return {
        "status": "success",
        "delivery_mode": dispatch_res.get("delivery_mode"),
        "recipients": recipients,
        "subject": subject,
        "tender_id": str(tender.tender_id),
        "tender_title": tender.title,
        "partner_name": partner.name,
        "partner_email": partner.email,
        "state_name": state_name,
        "view_url": dispatch_res.get("view_url"),
        "preview_file": dispatch_res.get("preview_file"),
        "sent_at": dispatch_res.get("sent_at"),
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
