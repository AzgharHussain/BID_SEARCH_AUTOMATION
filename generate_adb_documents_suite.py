import os
import json
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime
import pymupdf as fitz
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def calculate_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def sanitize_filename(name: str) -> str:
    import re
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()

def create_csrn_notice_pdf(pdf_path: Path, item: dict):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # US Letter
    
    # Header banner
    page.draw_rect(fitz.Rect(36, 36, 576, 85), color=(0.06, 0.23, 0.48), fill=(0.06, 0.23, 0.48))
    page.insert_text(fitz.Point(48, 60), "ASIAN DEVELOPMENT BANK (ADB)", fontsize=14, fontname="helv", color=(1, 1, 1))
    page.insert_text(fitz.Point(48, 76), "CONSULTANT MANAGEMENT SYSTEM (CMS) - OFFICIAL RECRUITMENT NOTICE", fontsize=8.5, fontname="helv", color=(0.85, 0.92, 1.0))

    y = 110
    page.insert_text(fitz.Point(36, y), "OFFICIAL CONSULTING OPPORTUNITY TITLE:", fontsize=8.5, fontname="helv", color=(0.3, 0.3, 0.3))
    y += 16
    page.insert_textbox(fitz.Rect(36, y, 576, y + 42), item.get("title", "Consulting Opportunity"), fontsize=11, fontname="helv", color=(0.05, 0.1, 0.25))
    y += 48

    fields = [
        ("Country / Beneficiary:", item.get("country", "Regional")),
        ("Package / Selection Number:", item.get("package_number", "PKG-ADB-AUTO")),
        ("Project / Loan Number:", item.get("project_number", "ADB-PROJECT")),
        ("Sector / Domain:", item.get("sector", "Multilateral Infrastructure & Geospatial")),
        ("Consultant Type:", item.get("consultant_type", "Firm")),
        ("Selection Method:", item.get("selection_method", "Quality and Cost-Based Selection (QCBS)")),
        ("Source Classification:", item.get("consultant_source", "International")),
        ("Proposal Format:", item.get("technical_proposal_type", "Full Technical Proposal (FTP)")),
        ("Disclosed Budget:", f"USD {float(item.get('budget_amount', 750000)):,.2f}" if item.get("budget_amount") else "Estimated USD 750,000.00"),
        ("Engagement Duration:", f"{item.get('duration_months', 12)} Months"),
        ("Executing Agency:", item.get("executing_agency", "Asian Development Bank / National Executing Agency")),
        ("Publication Date:", item.get("published_date_str", "2026")),
        ("Official EOI Deadline (Manila):", item.get("eoi_deadline_str", "2026 Manila local time (UTC+8)")),
        ("Converted Deadline (IST):", item.get("eoi_deadline_ist", "2026 (Indian Standard Time UTC+5:30)")),
        ("Contact Officer / Procurement Desk:", item.get("contact_officer", "ADB Multilateral Procurement Unit")),
        ("Official Portal Link:", "https://cms.adb.org/ | https://selfservice.adb.org/")
    ]

    for label, val in fields:
        page.draw_rect(fitz.Rect(36, y - 2, 576, y + 14), fill=(0.95, 0.96, 0.98) if (y // 18) % 2 == 0 else (1, 1, 1))
        page.insert_text(fitz.Point(42, y + 10), str(label), fontsize=8, fontname="helv", color=(0.2, 0.25, 0.35))
        page.insert_text(fitz.Point(230, y + 10), str(val)[:75], fontsize=8, fontname="helv", color=(0.05, 0.1, 0.15))
        y += 18

    y += 15
    page.draw_rect(fitz.Rect(36, y, 576, y + 2), fill=(0.06, 0.23, 0.48))
    y += 18
    page.insert_text(fitz.Point(36, y), "MANDATORY SUBMISSION REQUIREMENTS & NOTICE NOTES:", fontsize=9, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 16
    notes = (
        "1. Expressions of Interest (EOI) must be electronically submitted through the ADB Consultant Management System (CMS).\n"
        "2. Consulting firms must be legally incorporated in an ADB member country and maintain verified anti-corruption compliance.\n"
        "3. Joint Ventures / Consortia must designate a Lead Consultant and furnish written consortium intent agreements.\n"
        "4. All inquiries regarding this CSRN notice must be routed via CMS prior to the submission deadline."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 75), notes, fontsize=8.5, fontname="helv", color=(0.2, 0.2, 0.2))

    doc.save(str(pdf_path))
    doc.close()

def create_tor_pdf(pdf_path: Path, item: dict):
    doc = fitz.open()
    
    # Page 1: Objectives & Scope
    page1 = doc.new_page(width=612, height=792)
    page1.draw_rect(fitz.Rect(36, 36, 576, 80), color=(0.06, 0.23, 0.48), fill=(0.06, 0.23, 0.48))
    page1.insert_text(fitz.Point(48, 58), "TERMS OF REFERENCE (TOR) - TECHNICAL SCOPE", fontsize=13, fontname="helv", color=(1, 1, 1))
    page1.insert_text(fitz.Point(48, 74), f"Assignment: {item.get('title', 'Consulting Package')[:70]}", fontsize=8.5, fontname="helv", color=(0.85, 0.92, 1.0))

    y = 105
    page1.insert_text(fitz.Point(36, y), "1. ASSIGNMENT BACKGROUND & STRATEGIC OBJECTIVES", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    bg_text = (
        f"The Asian Development Bank (ADB), in coordination with the Executing Agency in {item.get('country', 'Regional')}, "
        f"requires the services of an experienced consulting firm to provide high-level professional advisory, geospatial analytics, "
        f"and technical implementation for {item.get('title', 'this project')}. The principal objective is to establish robust, "
        "sustainable, and climate-resilient spatial frameworks, ensuring strict adherence to ADB Safeguard Policy Statement (SPS) "
        "and international best engineering practices."
    )
    page1.insert_textbox(fitz.Rect(36, y, 576, y + 70), bg_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 80

    page1.insert_text(fitz.Point(36, y), "2. COMPREHENSIVE SCOPE OF WORK & WORK PACKAGES", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    scope_text = item.get("scope_of_work") or (
        "Work Package 1: Baseline Assessment, Data Collection & Spatial Data Infrastructure (SDI) Review.\n"
        "Work Package 2: Drone LiDAR / High-Resolution Satellite Data Ingestion, Vector Processing & CAD Conversion.\n"
        "Work Package 3: Development of Interactive WebGIS Geodatabase, Cloud Analytics & Real-Time Dashboards.\n"
        "Work Package 4: Institutional Strengthening, Technology Transfer, and Comprehensive User Training."
    )
    page1.insert_textbox(fitz.Rect(36, y, 576, y + 130), scope_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 145

    page1.insert_text(fitz.Point(36, y), "3. REQUIRED KEY EXPERTS & TEAM COMPOSITION", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    experts_text = (
        "• Team Leader / Senior Multilateral Project Manager (International, 12 Person-Months): Minimum 15 years in managing ADB/multilateral infrastructure projects.\n"
        "• Senior Geospatial / GIS Systems Architect (International/National, 10 Person-Months): Master's degree in Geoinformatics with expertise in enterprise spatial geodatabases.\n"
        "• Remote Sensing & Photogrammetry Specialist (National, 8 Person-Months): Extensive background in sub-meter satellite and drone LiDAR point cloud classification.\n"
        "• Environmental & Social Safeguards Specialist (National, 6 Person-Months): Specialist in ADB SPS 2009 and environmental management frameworks.\n"
        "• Full-Stack WebGIS Software Engineer (National, 8 Person-Months): Expert in React, Python, PostgreSQL/PostGIS, and MapLibre/OpenLayers."
    )
    page1.insert_textbox(fitz.Rect(36, y, 576, y + 150), experts_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 165

    page1.insert_text(fitz.Point(36, y), "4. DELIVERABLES, REPORTING SCHEDULE & MILESTONES", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    milestones_text = (
        "• Inception Report & Detailed Quality Assurance Plan (QAP) – Month 1\n"
        "• Baseline Spatial Data Infrastructure & Field Survey Report – Month 3\n"
        "• Draft Geospatial Analytics Engine & Interim System Demonstration – Month 6\n"
        "• Final Operational WebGIS Geoportal, User Manuals & Source Code Handover – Month 12"
    )
    page1.insert_textbox(fitz.Rect(36, y, 576, y + 80), milestones_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))

    doc.save(str(pdf_path))
    doc.close()

def create_boq_excel(excel_path: Path, item: dict):
    wb = openpyxl.Workbook()
    
    # Sheet 1: Summary of Costs
    ws1 = wb.active
    ws1.title = "Financial Summary"
    ws1.views.sheetView[0].showGridLines = True
    
    # Header styling
    hdr_fill = PatternFill(start_color="0F3B7A", end_color="0F3B7A", fill_type="solid")
    hdr_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    subhdr_fill = PatternFill(start_color="E6EDF5", end_color="E6EDF5", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True)
    normal_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='D0D7DE'),
        right=Side(style='thin', color='D0D7DE'),
        top=Side(style='thin', color='D0D7DE'),
        bottom=Side(style='thin', color='D0D7DE')
    )

    ws1.merge_cells("A1:E1")
    ws1["A1"] = f"ASIAN DEVELOPMENT BANK - FINANCIAL COST ESTIMATE & BOQ SCHEDULE"
    ws1["A1"].font = Font(name="Calibri", size=13, bold=True, color="0F3B7A")
    
    ws1.merge_cells("A2:E2")
    ws1["A2"] = f"Package: {item.get('package_number', 'N/A')} | Assignment: {item.get('title', 'N/A')[:60]}"
    ws1["A2"].font = Font(name="Calibri", size=9.5, italic=True, color="555555")

    headers = ["Item No.", "Cost Category / Expense Head", "Currency", "Estimated Amount", "% of Total"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws1.cell(row=4, column=col_idx, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    budget = float(item.get("budget_amount", 750000) or 750000)
    remun = round(budget * 0.58, 2)
    surveys = round(budget * 0.22, 2)
    oop = round(budget * 0.12, 2)
    contingency = round(budget * 0.08, 2)

    rows = [
        ("1.0", "Key Personnel & Non-Key Experts Remuneration", "USD", remun, "58.0%"),
        ("2.0", "Field Surveys, Drone LiDAR & Satellite Data Acquisition", "USD", surveys, "22.0%"),
        ("3.0", "Out-of-Pocket Expenses, Travel & Workshops", "USD", oop, "12.0%"),
        ("4.0", "Provisional Contingency Sums (8%)", "USD", contingency, "8.0%"),
        ("TOTAL", "TOTAL ESTIMATED PROPOSAL COST (EXCLUSIVE OF LOCAL TAXES)", "USD", budget, "100.0%")
    ]

    for r_idx, (num, cat, curr, amt, pct) in enumerate(rows, 5):
        is_total = (r_idx == 9)
        ws1.cell(row=r_idx, column=1, value=num).alignment = Alignment(horizontal="center")
        ws1.cell(row=r_idx, column=2, value=cat)
        ws1.cell(row=r_idx, column=3, value=curr).alignment = Alignment(horizontal="center")
        cell_amt = ws1.cell(row=r_idx, column=4, value=amt)
        cell_amt.number_format = '$#,##0.00'
        ws1.cell(row=r_idx, column=5, value=pct).alignment = Alignment(horizontal="center")

        for c_idx in range(1, 6):
            c = ws1.cell(row=r_idx, column=c_idx)
            c.border = thin_border
            if is_total:
                c.font = bold_font
                c.fill = subhdr_fill
            else:
                c.font = normal_font

    # Column widths
    ws1.column_dimensions["A"].width = 12
    ws1.column_dimensions["B"].width = 54
    ws1.column_dimensions["C"].width = 12
    ws1.column_dimensions["D"].width = 22
    ws1.column_dimensions["E"].width = 14

    # Sheet 2: Remuneration Breakdown
    ws2 = wb.create_sheet(title="Personnel Remuneration")
    ws2.views.sheetView[0].showGridLines = True
    ws2.merge_cells("A1:F1")
    ws2["A1"] = "SCHEDULE A: KEY PERSONNEL REMUNERATION BREAKDOWN"
    ws2["A1"].font = Font(name="Calibri", size=12, bold=True, color="0F3B7A")

    remun_headers = ["Staff Ref", "Expert Position", "Classification", "Input (PM)", "Monthly Rate (USD)", "Total Remuneration"]
    for col_idx, h in enumerate(remun_headers, 1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    staff_data = [
        ("K-1", "Team Leader & Project Management Specialist", "International", 12, 18500, 222000),
        ("K-2", "Senior Geospatial Systems Architect", "International", 8, 14000, 112000),
        ("K-3", "Remote Sensing & Photogrammetry Specialist", "National", 10, 5200, 52000),
        ("K-4", "Environmental & Social Safeguards Specialist", "National", 6, 4500, 27000),
        ("K-5", "Full-Stack WebGIS Software Engineer", "National", 8, 4200, 33600)
    ]

    for r_idx, s in enumerate(staff_data, 4):
        ws2.cell(row=r_idx, column=1, value=s[0]).alignment = Alignment(horizontal="center")
        ws2.cell(row=r_idx, column=2, value=s[1])
        ws2.cell(row=r_idx, column=3, value=s[2]).alignment = Alignment(horizontal="center")
        ws2.cell(row=r_idx, column=4, value=s[3]).alignment = Alignment(horizontal="center")
        c5 = ws2.cell(row=r_idx, column=5, value=s[4])
        c5.number_format = '$#,##0.00'
        c6 = ws2.cell(row=r_idx, column=6, value=s[5])
        c6.number_format = '$#,##0.00'
        for c_idx in range(1, 7):
            ws2.cell(row=r_idx, column=c_idx).border = thin_border
            ws2.cell(row=r_idx, column=c_idx).font = normal_font

    ws2.column_dimensions["A"].width = 12
    ws2.column_dimensions["B"].width = 44
    ws2.column_dimensions["C"].width = 16
    ws2.column_dimensions["D"].width = 14
    ws2.column_dimensions["E"].width = 20
    ws2.column_dimensions["F"].width = 22

    wb.save(str(excel_path))

def create_procurement_plan_pdf(pdf_path: Path, item: dict):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    page.draw_rect(fitz.Rect(36, 36, 576, 80), color=(0.06, 0.23, 0.48), fill=(0.06, 0.23, 0.48))
    page.insert_text(fitz.Point(48, 58), "ASIAN DEVELOPMENT BANK - PROJECT PROCUREMENT DATA SHEET", fontsize=12, fontname="helv", color=(1, 1, 1))
    page.insert_text(fitz.Point(48, 74), f"Country / Program: {item.get('country', 'Regional')} | Package: {item.get('package_number', 'N/A')}", fontsize=8.5, fontname="helv", color=(0.85, 0.92, 1.0))

    y = 105
    page.insert_text(fitz.Point(36, y), "1. PROCUREMENT FRAMEWORK & APPLICABLE REGULATIONS", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    reg_text = (
        "Procurement for this assignment will be carried out in accordance with the ADB Procurement Regulations for ADB "
        "Borrowers (2017, as amended from time to time). Quality and Cost-Based Selection (QCBS) with a 90:10 technical-to-financial "
        "weighting is mandated to ensure supreme technical expertise in geospatial and infrastructure modeling."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 60), reg_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 70

    page.insert_text(fitz.Point(36, y), "2. PROCUREMENT PLAN SUMMARY TABLE", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14

    plan_rows = [
        ("Project Country:", item.get("country", "Regional")),
        ("Executing Agency:", item.get("executing_agency", "Asian Development Bank")),
        ("Implementing Agency:", item.get("implementing_agency", "National Implementing Directorate")),
        ("Procurement Method:", item.get("selection_method", "QCBS (Quality & Cost Based)")),
        ("Review Type:", "Prior Review (ADB Headquarters / Resident Mission)"),
        ("Advertisement Portal:", "ADB CMS (cms.adb.org) & UN Development Business (UNDB)"),
        ("Advance Contracting:", "Yes (Shortlisting prior to loan effectiveness)"),
        ("Domestic Preference:", "Not Applicable (Open International Competition)")
    ]

    for label, val in plan_rows:
        page.draw_rect(fitz.Rect(36, y - 2, 576, y + 14), fill=(0.95, 0.96, 0.98) if (y // 18) % 2 == 0 else (1, 1, 1))
        page.insert_text(fitz.Point(42, y + 10), str(label), fontsize=8, fontname="helv", color=(0.2, 0.25, 0.35))
        page.insert_text(fitz.Point(230, y + 10), str(val), fontsize=8, fontname="helv", color=(0.05, 0.1, 0.15))
        y += 18

    y += 20
    page.insert_text(fitz.Point(36, y), "3. ANTI-CORRUPTION & SANCTIONS SCREENING", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    sanction_text = (
        "In accordance with ADB Anticorruption Policy, consulting entities and their associates are subjected to rigorous "
        "sanctions screening against the ADB Complete Sanctions List and the Cross-Debarment Register established under the "
        "Agreement for Mutual Enforcement of Debarment Decisions among Multilateral Development Banks (MDBs)."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 60), sanction_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))

    doc.save(str(pdf_path))
    doc.close()

def create_eoi_template_pdf(pdf_path: Path, item: dict):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    page.draw_rect(fitz.Rect(36, 36, 576, 80), color=(0.06, 0.23, 0.48), fill=(0.06, 0.23, 0.48))
    page.insert_text(fitz.Point(48, 58), "ASIAN DEVELOPMENT BANK - EXPRESSION OF INTEREST (EOI) FORM", fontsize=12, fontname="helv", color=(1, 1, 1))
    page.insert_text(fitz.Point(48, 74), f"Standard EOI Submission Template | TECH-1 to TECH-6 | Package: {item.get('package_number', 'N/A')}", fontsize=8.5, fontname="helv", color=(0.85, 0.92, 1.0))

    y = 105
    page.insert_text(fitz.Point(36, y), "FORM TECH-1: EXPRESSION OF INTEREST SUBMISSION LETTER", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    tech1 = (
        "To: The Project Director / ADB Procurement Committee\n\n"
        f"We, the undersigned, offer to provide the consulting services for '{item.get('title', 'this project')}' "
        f"under Package No. {item.get('package_number', 'N/A')} in accordance with your published CSRN notice. "
        "We are hereby submitting our Expression of Interest through the ADB Consultant Management System (CMS).\n\n"
        "We hereby declare that all the information and statements made in this EOI are true and correct, and we accept "
        "that any misinterpretation contained in it may lead to our disqualification."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 100), tech1, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 115

    page.insert_text(fitz.Point(36, y), "FORM TECH-2: CONSULTANT'S ORGANIZATION & RECENT ASSIGNMENTS", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    tech2 = (
        "• Brief description of the firm's legal status, corporate governance, and core technical competencies.\n"
        "• Summary of relevant assignments completed in the past 10 years demonstrating technical leadership in "
        "geospatial data systems, webgeoportals, and multilateral infrastructure monitoring."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 55), tech2, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 70

    page.insert_text(fitz.Point(36, y), "FORM TECH-3: PROPOSED TECHNICAL APPROACH & WORK PLAN", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    tech3 = (
        "Consultant must present a clear, articulated methodology covering:\n"
        "a) Technical approach to satellite imagery ingestion, vector digitizing & spatial analytics.\n"
        "b) Work plan showing activity sequence, milestone delivery dates, and quality checkpoints.\n"
        "c) Organization and staffing schedule indicating person-months allocated to each key expert."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 70), tech3, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))

    doc.save(str(pdf_path))
    doc.close()

def create_integrity_declaration_pdf(pdf_path: Path, item: dict):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    
    page.draw_rect(fitz.Rect(36, 36, 576, 80), color=(0.06, 0.23, 0.48), fill=(0.06, 0.23, 0.48))
    page.insert_text(fitz.Point(48, 58), "ASIAN DEVELOPMENT BANK - INTEGRITY & SANCTIONS COMPLIANCE", fontsize=12, fontname="helv", color=(1, 1, 1))
    page.insert_text(fitz.Point(48, 74), "MANDATORY COMPLIANCE DECLARATION & CODE OF INTEGRITY", fontsize=8.5, fontname="helv", color=(0.85, 0.92, 1.0))

    y = 105
    page.insert_text(fitz.Point(36, y), "1. DECLARATION OF COMPLIANCE WITH ADB ANTICORRUPTION POLICY", fontsize=9.5, fontname="helv", color=(0.06, 0.23, 0.48))
    y += 14
    body = (
        "The Consultant hereby solemnly affirms and declares that:\n\n"
        "1. Anticorruption Compliance: The Consultant has not engaged in, and will not engage in, corrupt, fraudulent, "
        "collusive, coercive, or obstructive practices as defined in ADB Anticorruption Policy (1998, as amended).\n\n"
        "2. Sanctions List Verification: Neither the Consultant, nor any of its consortium partners, subconsultants, or "
        "key personnel are currently debarred or suspended by ADB, the World Bank, or any multilateral development bank.\n\n"
        "3. Conflict of Interest: The Consultant confirms there exists no actual, potential, or perceived conflict of interest "
        "in undertaking the proposed services for this ADB procurement.\n\n"
        "4. Audit & Verification: The Consultant explicitly permits ADB and its appointed representatives to inspect all "
        "accounts, records, and other documents relating to the submission of this EOI and proposal execution."
    )
    page.insert_textbox(fitz.Rect(36, y, 576, y + 170), body, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
    y += 190

    # Signature block
    page.draw_rect(fitz.Rect(36, y, 576, y + 95), fill=(0.97, 0.98, 0.99), color=(0.8, 0.85, 0.9))
    page.insert_text(fitz.Point(48, y + 20), "AUTHORIZED CORPORATE SIGNATORY", fontsize=9, fontname="helv", color=(0.06, 0.23, 0.48))
    page.insert_text(fitz.Point(48, y + 40), "Name & Title: Authorized Managing Director / Principal Partner", fontsize=8.5, fontname="helv", color=(0.2, 0.2, 0.2))
    page.insert_text(fitz.Point(48, y + 56), "Corporate Identity: GISFY Private Limited & Consortium Partners", fontsize=8.5, fontname="helv", color=(0.2, 0.2, 0.2))
    page.insert_text(fitz.Point(48, y + 72), f"Date of Execution: {datetime.utcnow().strftime('%d %B %Y')} | Verified via ADB CMS Gateway", fontsize=8.5, fontname="helv", color=(0.2, 0.2, 0.2))

    doc.save(str(pdf_path))
    doc.close()

def create_bundle_zip(zip_path: Path, doc_files: list, item: dict):
    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = {
            "title": item.get("title"),
            "country": item.get("country"),
            "package_number": item.get("package_number"),
            "eoi_deadline": item.get("eoi_deadline_str"),
            "generated_at": datetime.utcnow().isoformat(),
            "documents": []
        }
        for f in doc_files:
            if f.exists():
                zf.write(str(f), arcname=f.name)
                manifest["documents"].append({
                    "file_name": f.name,
                    "size_bytes": f.stat().st_size,
                    "sha256_hash": calculate_sha256(f)
                })
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
