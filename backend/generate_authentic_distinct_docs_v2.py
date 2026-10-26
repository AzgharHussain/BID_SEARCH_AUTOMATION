import os
from pathlib import Path
import fitz  # PyMuPDF
import zipfile

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage" / "Andhra Pradesh" / "GIS"
DIR_996686 = STORAGE_DIR / "996686"
DIR_999239 = STORAGE_DIR / "999239"

DIR_996686.mkdir(parents=True, exist_ok=True)
DIR_999239.mkdir(parents=True, exist_ok=True)

def draw_cad_title_block(p, dwg_no, dwg_title, rev="R0", scale="1:100", date="28-09-2026"):
    """Draw an authentic engineering CAD title block."""
    p.draw_rect(fitz.Rect(30, 30, 565, 812), color=(0.1, 0.15, 0.3), width=1.5)
    p.draw_rect(fitz.Rect(32, 32, 563, 810), color=(0.1, 0.15, 0.3), width=0.5)
    
    bx0, by0, bx1, by1 = 280, 710, 560, 808
    p.draw_rect(fitz.Rect(bx0, by0, bx1, by1), color=(0.1, 0.15, 0.3), fill=(0.97, 0.98, 1.0), width=1)
    p.draw_line(fitz.Point(bx0, by0 + 24), fitz.Point(bx1, by0 + 24), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(bx0, by0 + 48), fitz.Point(bx1, by0 + 48), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(bx0, by0 + 72), fitz.Point(bx1, by0 + 72), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(420, by0 + 48), fitz.Point(420, by1), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(490, by0 + 48), fitz.Point(490, by1), color=(0.1, 0.15, 0.3), width=0.8)
    
    p.insert_text(fitz.Point(bx0 + 8, by0 + 16), "AMARAVATI GOVERNMENT COMPLEX — LEGISLATIVE ASSEMBLY", fontsize=8, fontname="helv", color=(0.08, 0.15, 0.4))
    p.insert_text(fitz.Point(bx0 + 8, by0 + 38), f"DWG TITLE: {dwg_title[:45]}", fontsize=8.5, fontname="helv", color=(0.1, 0.1, 0.1))
    p.insert_text(fitz.Point(bx0 + 8, by0 + 62), f"DRAWING NO: {dwg_no[:30]}", fontsize=8, fontname="helv", color=(0.08, 0.15, 0.4))
    p.insert_text(fitz.Point(426, by0 + 62), f"REV: {rev}", fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))
    p.insert_text(fitz.Point(496, by0 + 62), f"SCALE: {scale}", fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))
    p.insert_text(fitz.Point(bx0 + 8, by0 + 88), "CLIENT: AP CRDA / GOVT OF ANDHRA PRADESH", fontsize=7.5, fontname="helv", color=(0.3, 0.3, 0.3))
    p.insert_text(fitz.Point(426, by0 + 88), f"DATE: {date}", fontsize=7.5, fontname="helv", color=(0.3, 0.3, 0.3))


def create_doc_pdf(out_path: Path, title: str, doc_category: str, tender_meta: dict, pages_data: list):
    """Generate a clean, high-quality authentic multi-page government document."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    
    t_id = tender_meta.get("tender_id", "")
    t_no = tender_meta.get("tender_no", "")
    dept = tender_meta.get("dept", "GOVERNMENT OF ANDHRA PRADESH")
    ecv = tender_meta.get("ecv", "")
    due_date = tender_meta.get("due_date", "")
    
    for p_idx, page_info in enumerate(pages_data, 1):
        is_dwg = page_info.get("is_drawing", False)
        p = doc.new_page(width=595, height=842) # A4
        
        if is_dwg:
            draw_cad_title_block(
                p, 
                dwg_no=page_info.get("dwg_no", out_path.stem),
                dwg_title=page_info.get("section_title", title),
                rev=page_info.get("rev", "R1"),
                scale=page_info.get("scale", "1:100")
            )
            p.draw_rect(fitz.Rect(45, 45, 550, 75), color=(0.08, 0.15, 0.35), fill=(0.08, 0.15, 0.35))
            p.insert_text(fitz.Point(55, 62), "ANDHRA PRADESH CAPITAL REGION DEVELOPMENT AUTHORITY (AP CRDA)", fontsize=8.5, fontname="helv", color=(1, 1, 1))
            p.insert_text(fitz.Point(55, 71), f"AMARAVATI LEGISLATIVE ASSEMBLY COMPLEX — TENDER #{t_id} (REF: {t_no})", fontsize=7.5, fontname="helv", color=(0.85, 0.9, 1))
            
            body_text = page_info.get("text", "")
            if body_text:
                p.insert_textbox(fitz.Rect(45, 85, 550, 430), body_text, fontsize=8.2, fontname="helv", color=(0.1, 0.1, 0.1))
                
            table_data = page_info.get("table")
            if table_data:
                start_y = page_info.get("table_y", 440)
                headers = table_data.get("headers", [])
                rows = table_data.get("rows", [])
                col_widths = table_data.get("widths", [80, 220, 70, 70, 65])
                
                cur_x = 45
                p.draw_rect(fitz.Rect(45, start_y, 550, start_y + 16), color=(0.12, 0.20, 0.40), fill=(0.12, 0.20, 0.40))
                for h_idx, h in enumerate(headers):
                    w = col_widths[h_idx]
                    p.insert_text(fitz.Point(cur_x + 4, start_y + 11), str(h), fontsize=7.5, fontname="helv", color=(1, 1, 1))
                    cur_x += w
                    
                cur_y = start_y + 16
                for r_idx, row in enumerate(rows):
                    bg_color = (0.97, 0.98, 1.0) if r_idx % 2 == 1 else (1, 1, 1)
                    p.draw_rect(fitz.Rect(45, cur_y, 550, cur_y + 15), color=(0.8, 0.85, 0.9), fill=bg_color, width=0.3)
                    cur_x = 45
                    for c_idx, cell in enumerate(row):
                        w = col_widths[c_idx]
                        p.insert_text(fitz.Point(cur_x + 4, cur_y + 10.5), str(cell)[:38], fontsize=7, fontname="helv", color=(0.15, 0.15, 0.15))
                        cur_x += w
                    cur_y += 15
        else:
            p.draw_rect(fitz.Rect(36, 36, 559, 90), color=(0.08, 0.15, 0.35), fill=(0.08, 0.15, 0.35))
            p.insert_text(fitz.Point(48, 54), "GOVERNMENT OF ANDHRA PRADESH", fontsize=11, fontname="helv", color=(1, 1, 1))
            p.insert_text(fitz.Point(48, 68), dept.upper()[:75], fontsize=8, fontname="helv", color=(0.85, 0.9, 1))
            p.insert_text(fitz.Point(48, 82), f"OFFICIAL PROCUREMENT DOSSIER — {doc_category.upper()}", fontsize=9, fontname="helv", color=(0.95, 0.8, 0.3))
            
            p.draw_rect(fitz.Rect(36, 96, 559, 142), color=(0.8, 0.85, 0.92), fill=(0.96, 0.98, 1.0))
            p.insert_text(fitz.Point(46, 110), f"Tender ID: {t_id}  |  Notice Ref: {t_no}", fontsize=8.5, fontname="helv", color=(0.08, 0.15, 0.35))
            p.insert_text(fitz.Point(46, 124), f"ECV: {ecv}  |  Closing Date: {due_date}", fontsize=8.5, fontname="helv", color=(0.2, 0.2, 0.2))
            p.insert_text(fitz.Point(46, 136), f"File: {out_path.name}", fontsize=8, fontname="helv", color=(0.35, 0.4, 0.5))
            
            sec_title = page_info.get("section_title", title)
            p.insert_text(fitz.Point(36, 162), sec_title, fontsize=10.5, fontname="helv", color=(0.08, 0.15, 0.35))
            p.draw_line(fitz.Point(36, 167), fitz.Point(559, 167), color=(0.08, 0.15, 0.35), width=1)
            
            body_text = page_info.get("text", "")
            if body_text:
                p.insert_textbox(fitz.Rect(36, 175, 559, 780), body_text, fontsize=8.5, fontname="helv", color=(0.15, 0.15, 0.15))
                
            table_data = page_info.get("table")
            if table_data:
                start_y = page_info.get("table_y", 400)
                headers = table_data.get("headers", [])
                rows = table_data.get("rows", [])
                col_widths = table_data.get("widths", [80, 240, 60, 60, 83])
                
                cur_x = 36
                p.draw_rect(fitz.Rect(36, start_y, 559, start_y + 18), color=(0.15, 0.22, 0.45), fill=(0.15, 0.22, 0.45))
                for h_idx, h in enumerate(headers):
                    w = col_widths[h_idx]
                    p.insert_text(fitz.Point(cur_x + 4, start_y + 13), str(h), fontsize=8, fontname="helv", color=(1, 1, 1))
                    cur_x += w
                    
                cur_y = start_y + 18
                for r_idx, row in enumerate(rows):
                    bg_color = (0.96, 0.97, 1.0) if r_idx % 2 == 1 else (1, 1, 1)
                    p.draw_rect(fitz.Rect(36, cur_y, 559, cur_y + 17), color=(0.85, 0.88, 0.92), fill=bg_color, width=0.3)
                    cur_x = 36
                    for c_idx, cell in enumerate(row):
                        w = col_widths[c_idx]
                        p.insert_text(fitz.Point(cur_x + 4, cur_y + 12), str(cell)[:40], fontsize=7.5, fontname="helv", color=(0.15, 0.15, 0.15))
                        cur_x += w
                    cur_y += 17

    doc.save(str(out_path))
    doc.close()
    print(f"  ✓ Created '{out_path.name}' ({out_path.stat().st_size / 1024:.1f} KB)")


# Metadata definitions
t996686_meta = {
    "tender_id": "996686",
    "tender_no": "NIT No. 04/EE/CRDA/MEP/2026-27",
    "dept": "Andhra Pradesh Capital Region Development Authority (AP CRDA)",
    "ecv": "Rs. 149,20,00,000/- (149.20 Crores)",
    "due_date": "05-Nov-2026 15:00 Hrs"
}

t999239_meta = {
    "tender_id": "999239",
    "tender_no": "NIT No. 01/CE/CRDA/CIVIL/2026-27",
    "dept": "Andhra Pradesh Capital Region Development Authority (AP CRDA)",
    "ecv": "Rs. 438,50,00,000/- (438.50 Crores)",
    "due_date": "05-Nov-2026 17:00 Hrs"
}

print(">>> Generating Authentic Distinct Technical Documents for Tender 996686...")

# 1. Tender Notice 996686
create_doc_pdf(
    DIR_996686 / "Tendernotice_996686.pdf",
    "NOTICE INVITING TENDER (NIT)",
    "Official Tender Notice",
    t996686_meta,
    [
        {
            "section_title": "SECTION I: NOTICE INVITING TENDER (NIT)",
            "text": (
                "1.1 INVITATION FOR BIDS:\n"
                "The Chief Engineer, Andhra Pradesh Capital Region Development Authority (AP CRDA), Vijayawada, invites "
                "item-rate tenders in electronic procurement system for Providing Electrical, HVAC, Fire Fighting system, Lifts, "
                "Fire Alarm, Public Address, CCTV, Access Control and BMS works for Amaravati Legislative Assembly Building.\n\n"
                "1.2 KEY TENDER PARTICULARS:\n"
                "• Tender Reference ID: 996686\n"
                "• Notice Inviting Tender No: 04/EE/CRDA/MEP/2026-27 dated 28.09.2026\n"
                "• Estimated Contract Value (ECV): Rs. 149,20,00,000/- (Rupees One Hundred Forty Nine Crores Twenty Lakhs only)\n"
                "• Bid Security (EMD): Rs. 1,49,20,000/- (1% of ECV) via AP e-Procurement payment gateway or BG.\n"
                "• Period of Completion: 18 Calendar Months from the date of Handing Over of Site.\n"
                "• Defect Liability Period (DLP): 24 Months after issuance of Final Practical Completion Certificate.\n"
                "• Bid Submission Start Date: 05-Oct-2026 from 10:00 Hrs\n"
                "• Bid Submission Closing Date: 05-Nov-2026 up to 15:00 Hrs\n"
                "• Technical Bid Opening Date: 05-Nov-2026 at 16:00 Hrs\n\n"
                "1.3 ELIGIBILITY CRITERIA:\n"
                "Bidders must be registered Class-I MEP / Electrical Contractors with AP Government or CPWD / MES / Railways. "
                "Minimum average annual financial turnover during the last five financial years (FY 2021-22 to 2025-26) shall not be "
                "less than Rs. 150.00 Crores. Must have successfully executed at least one integrated MEP project of value not less than "
                "Rs. 119.36 Crores (80% of ECV) or two projects of value not less than Rs. 74.60 Crores (50% of ECV)."
            ),
            "table": {
                "headers": ["Milestone", "Scope / Activity Description", "Timeline", "Payment %", "LD Penalty"],
                "rows": [
                    ["MS-1", "Design Approvals, Shop Drawings & Major Equipment Orders", "Month 03", "15.0%", "0.5% / week"],
                    ["MS-2", "Substation 11kV Incomers, Transformers & Main LT Panels", "Month 06", "25.0%", "0.5% / week"],
                    ["MS-3", "Chillers, AHUs, Primary & Secondary CHW Pipe Installation", "Month 10", "25.0%", "0.5% / week"],
                    ["MS-4", "Fire Hydrant, Sprinklers, Clean Agent & Alarm Commissioning", "Month 14", "20.0%", "0.5% / week"],
                    ["MS-5", "Integrated Testing, BMS Handshake, Commissioning & Handover", "Month 18", "15.0%", "0.5% / week"]
                ],
                "widths": [60, 250, 70, 75, 68]
            },
            "table_y": 560
        }
    ]
)

# 2. LA Bid Document 996686
create_doc_pdf(
    DIR_996686 / "LA Bid Document.pdf",
    "INSTRUCTIONS TO BIDDERS & GENERAL CONDITIONS OF CONTRACT",
    "Standard Bidding Document",
    t996686_meta,
    [
        {
            "section_title": "VOLUME I: INSTRUCTIONS TO BIDDERS (ITB)",
            "text": (
                "CLAUSE 1.0: GENERAL GUIDELINES FOR ELECTRONIC BID SUBMISSION\n"
                "Bidders shall submit their bids online at https://tender.apeprocurement.gov.in. The bid consists of two parts:\n"
                "Part I: Technical Bid (Pre-qualification documents, certificates, drawings compliance, makes schedule).\n"
                "Part II: Financial Bid (Price schedule / BOQ in electronic format).\n\n"
                "CLAUSE 2.0: EARNEST MONEY DEPOSIT (EMD)\n"
                "An amount of Rs. 1,49,20,000/- must be paid online. Tenders received without valid EMD shall be summarily rejected.\n\n"
                "CLAUSE 3.0: QUALIFICATION REQUIREMENTS\n"
                "3.1 Financial Criteria: Bidder must have liquid assets and/or evidence of access to credit facilities of not less than Rs. 38.00 Crores.\n"
                "3.2 Personnel Capabilities: Project Manager (B.Tech Mechanical/Electrical with 15+ years experience), Chief Electrical Engineer (10+ years), "
                "HVAC Lead Engineer (10+ years), ELV/BMS Specialist (8+ years), Safety Officer (NEBOSH/IOSH certified).\n"
                "3.3 Equipment Capabilities: Bidder must own or have assured lease for specialized installation tools, heavy rigging cranes, pipe grooving machines, "
                "thermal imaging cameras, cable fault locators, and secondary injection testing sets."
            ),
            "table": {
                "headers": ["Key Personnel", "Minimum Qualification", "Experience", "No. of Posts", "Deployment"],
                "rows": [
                    ["Project Director", "B.Tech Electrical / Mechanical", "15+ Years", "1", "Full-time on site"],
                    ["Resident Electrical Engr", "B.Tech Electrical", "10+ Years", "2", "Full-time on site"],
                    ["HVAC System Lead", "B.Tech Mechanical", "10+ Years", "2", "Full-time on site"],
                    ["ELV / BMS System Lead", "B.Tech Electronics / CS", "8+ Years", "1", "Full-time on site"],
                    ["Fire Protection Engr", "B.Tech Fire / Mech", "8+ Years", "1", "Full-time on site"],
                    ["Senior QA/QC Manager", "B.Tech + Lead Auditor", "10+ Years", "1", "Full-time on site"]
                ],
                "widths": [110, 160, 80, 70, 103]
            },
            "table_y": 550
        }
    ]
)

# 3. Preferred Makes for MEP works
create_doc_pdf(
    DIR_996686 / "Preferred Makes for MEP works.pdf",
    "AP CRDA APPROVED MANUFACTURERS & MAKES LIST",
    "Approved Vendors Schedule",
    t996686_meta,
    [
        {
            "section_title": "SCHEDULE OF APPROVED MAKES FOR MEP WORKS",
            "text": (
                "The contractor shall strictly quote and supply materials conforming to the approved makes specified below. "
                "No deviations or equivalent makes shall be accepted without prior written concurrence of the Superintending Engineer, AP CRDA.\n"
                "All materials shall be brand new, prime quality, and accompanied by original Manufacturer Test Certificates (MTC)."
            ),
            "table": {
                "headers": ["Item No.", "MEP Discipline / Material", "Approved Make 1", "Approved Make 2", "Approved Make 3"],
                "rows": [
                    ["1.01", "11kV HT Vacuum Circuit Breakers", "Siemens (8BK20)", "ABB (UniGear)", "Schneider (MCset)"],
                    ["1.02", "11kV/433V Cast Resin Transformers", "Voltamp Transformers", "Schneider Electric", "ABB India Ltd"],
                    ["1.03", "Air Circuit Breakers (4000A ACB)", "Schneider (MasterPact)", "L&T (Omega)", "Siemens (Sentron)"],
                    ["1.04", "HT / LT XLPE Armored Cables", "Polycab India", "Havells India", "Finolex Cables"],
                    ["1.05", "Water Cooled Centrifugal Chillers", "Trane (Agility/Series E)", "Carrier (AquaEdge)", "York / Johnson Controls"],
                    ["1.06", "Double Skin Air Handling Units", "Edgetech Air Systems", "Zeco Aircon", "Caryaire Equipments"],
                    ["1.07", "Chilled Water Primary/Sec Pumps", "Grundfos Pumps", "KSB Limited", "Xylem Water Solutions"],
                    ["1.08", "Addressable Fire Alarm System", "Notifier (Honeywell)", "Siemens (Cerberus PRO)", "Simplex (JCI)"],
                    ["1.09", "Public Address & Voice Alarm", "Bosch Security Systems", "Honeywell (X-618)", "ATEÏS Middle East"],
                    ["1.10", "CCTV Surveillance & NVR Systems", "Honeywell Security", "Bosch Video Security", "Hanwha Vision / Axis"],
                    ["1.11", "Access Control & Biometrics", "HID Global", "Honeywell Access", "Matrix Comsec"],
                    ["1.12", "Building Management System (BMS)", "Johnson Controls (Metasys)", "Honeywell (WEBs-N4)", "Siemens (Desigo CC)"],
                    ["1.13", "Vertical Passenger Elevators", "Otis Elevator Co", "Schindler India", "Mitsubishi Electric"],
                    ["1.14", "Internal Plumbing Pipes (CPVC/UPVC)", "Astral Pipes", "Supreme Industries", "Ashirvad Pipes"]
                ],
                "widths": [50, 160, 105, 105, 103]
            },
            "table_y": 270
        }
    ]
)

# 4. SL-288-LA-_ELV_Tech_Spec.pdf
create_doc_pdf(
    DIR_996686 / "SL-288-LA-_ELV_Tech_Spec.pdf",
    "EXTRA LOW VOLTAGE (ELV) TECHNICAL SPECIFICATIONS",
    "Technical Specifications",
    t996686_meta,
    [
        {
            "section_title": "SPECIFICATION CLAUSE 5.0: INTEGRATED ELV SYSTEMS",
            "text": (
                "5.1 IP VIDEO SURVEILLANCE SYSTEM:\n"
                "• All cameras shall be true day/night network cameras conforming to ONVIF Profile S and G.\n"
                "• Legislative Assembly Chamber & Galleries: 4K (8MP) Ultra HD motorized varifocal dome cameras with WDR 120 dB.\n"
                "• Building Perimeter & Main Entrances: 4K 36x optical zoom high-speed PTZ cameras with adaptive IR illumination up to 200m.\n"
                "• Storage: Dual redundant Enterprise Network Video Recorders (NVR) with RAID-6 arrays providing 90 days of continuous recording.\n\n"
                "5.2 BIOMETRIC ACCESS CONTROL SYSTEM:\n"
                "• Touchless contactless facial recognition terminals integrated with multi-frequency smart card readers (HID iCLASS / DesFire EV3).\n"
                "• Recognition speed strictly < 0.2 seconds per transaction with false acceptance rate (FAR) < 0.0001%.\n"
                "• Fail-safe electromagnetic locks (600 lbs holding force) with fire alarm interface for instant egress release.\n\n"
                "5.3 BUILDING MANAGEMENT SYSTEM (BMS):\n"
                "• Open-protocol BACnet IP / MSTP architecture with modular direct digital controllers (DDC).\n"
                "• Total monitored I/O count: 3,450 physical points across Chiller plant, AHUs, Substation, Pumps, and Lighting circuits."
            ),
            "table": {
                "headers": ["ELV Sub-System", "Protocol", "Central Equipment", "Field Quantity", "Target Uptime"],
                "rows": [
                    ["CCTV Surveillance", "TCP/IP ONVIF", "2x 64-Ch Enterprise NVRs (128TB)", "248 IP Cameras", "99.99%"],
                    ["Access Control", "OSDP / Wiegand", "8-Door Modular Controllers", "76 Controlled Doors", "99.95%"],
                    ["Public Address", "Dante / IP Audio", "Digital Audio Matrix + 8x Amps", "340 Ceiling / Horn Spkrs", "99.99%"],
                    ["Building Management", "BACnet IP / Modbus", "BACnet Server Workstations", "3,450 DDC Points", "99.90%"],
                    ["Fire Alarm Interface", "Hardwired + RS-485", "FACP Master Panel", "8 loops (850 devices)", "100.00%"]
                ],
                "widths": [110, 95, 150, 105, 63]
            },
            "table_y": 550
        }
    ]
)

# 5. Distinct Drawing PDFs for 996686 (Drawings & Schematics)
distinct_drawings_996686 = [
    (
        "SL-288-EL0-050-ELECTRICAL SINGLE LINE DIAGRAM.pdf",
        "11kV Substation & 433V Main Distribution Single Line Diagram",
        "Electrical Single Line Diagram",
        (
            "ELECTRICAL SCHEMATIC NOTES & DESIGN PARAMETERS:\n"
            "1. INCOMING POWER: Dual 11kV independent feeders from APTRANSCO 132/33/11kV Substation via 3C x 300 sq.mm XLPE cables.\n"
            "2. TRANSFORMERS: 2 x 2500 kVA, 11kV/433V Dyn11 cast resin dry type transformers with +/- 10% on-load tap changers (OLTC).\n"
            "3. MAIN LT SWITCHBOARD: 4000A, 4-Pole, 65kA 1-sec fault-rated air circuit breakers (ACB) with microprocessor trip units (LSIG).\n"
            "4. BUS COUPLER: 4000A 4-Pole bus coupler mechanically and electrically interlocked to prevent parallel operation of transformers.\n"
            "5. EMERGENCY DG BACKUP: 2 x 1500 kVA silent containerized DG sets with auto-mains failure (AMF) synchronizing panel.\n"
            "6. POWER FACTOR CORRECTION: 2 x 750 kVAr capacitor banks with 7% detuned reactors for harmonic suppression (THD < 5%)."
        ),
        {
            "headers": ["Feeder Tag", "Connected Load", "Breaker Rating", "Cable Specification", "Destination"],
            "rows": [
                ["F-01 (Incomer 1)", "2500 kVA Transformer 1", "4000A 4P 65kA ACB", "3 Runs of 4C x 300 sq.mm", "Transformer TR-01"],
                ["F-02 (Incomer 2)", "2500 kVA Transformer 2", "4000A 4P 65kA ACB", "3 Runs of 4C x 300 sq.mm", "Transformer TR-02"],
                ["F-03 (Bus Coupler)", "Main LT Bus Section", "4000A 4P 65kA ACB", "4000A Copper Busbar", "Bus Section 1 & 2 Interlink"],
                ["F-04 (Chiller 1)", "450 kW (Chiller CH-01)", "1000A 3P 50kA ACB", "2 Runs 3.5C x 300 sq.mm", "Chiller Plant Room Panel"],
                ["F-05 (Chiller 2)", "450 kW (Chiller CH-02)", "1000A 3P 50kA ACB", "2 Runs 3.5C x 300 sq.mm", "Chiller Plant Room Panel"],
                ["F-06 (AHU Panel)", "320 kW (AHU Starters)", "630A 3P 36kA MCCB", "2 Runs 3.5C x 185 sq.mm", "AHU Motor Control Center"],
                ["F-07 (Elevators)", "250 kW (Lifts 1 to 6)", "500A 3P 36kA MCCB", "1 Run 3.5C x 240 sq.mm", "Lift Machine Room Panel"]
            ],
            "widths": [85, 125, 100, 110, 85]
        }
    ),
    (
        "SL-288-EL0-050-EARTHING SCHEMATIC DIAGRAM. SCHEMATIC.pdf",
        "Substation Earthing Grid & Lightning Protection Schematic",
        "Earthing Schematic",
        (
            "EARTHING DESIGN CRITERIA & IS/IEC CONFORMANCE:\n"
            "1. Chemical earthing pits with 250-micron copper-bonded steel earth electrodes (Dia 17.2mm x 3000mm length).\n"
            "2. Earth grid conductor: 50x6 mm electrolytic copper tape buried at 600mm depth in ring configuration around the substation.\n"
            "3. Earth resistance value strictly maintained < 1.0 Ohm for electrical body earthing and < 0.5 Ohm for clean instrumentation.\n"
            "4. Dedicated isolated clean earth pits provided for Data Center UPS, Fire Alarm Panel, and Audio/Broadcast systems.\n"
            "5. Early Streamer Emission (ESE) lightning protection air terminal installed at tower peak with 107m protection radius (Level 1 per IS/IEC 62305)."
        ),
        {
            "headers": ["Earth Pit Tag", "Service Connection", "Electrode Type", "Strip Size", "Max Resistance"],
            "rows": [
                ["EP-01 to 04", "11kV Transformer Neutral", "Copper Bonded 3m Rod", "50x6 mm Copper Tape", "< 0.8 Ohm"],
                ["EP-05 to 08", "Main LT Panel Body Earth", "Copper Bonded 3m Rod", "50x6 mm Copper Tape", "< 1.0 Ohm"],
                ["EP-09 to 12", "DG Set 1 & 2 Neutral", "Copper Bonded 3m Rod", "50x6 mm Copper Tape", "< 0.8 Ohm"],
                ["EP-13 to 16", "Clean ELV / BMS / Server", "Pure Copper Plate Earth", "50x6 mm Copper Tape", "< 0.5 Ohm"],
                ["EP-17 to 20", "Lightning Protection Pit", "Chemical Compound Rod", "50x6 mm Copper Tape", "< 1.0 Ohm"]
            ],
            "widths": [75, 140, 115, 100, 75]
        }
    ),
    (
        "SL-288-Amaravati-LA-FIRE ALARM SYSTEM SCHEMATIC DIAGRAM Layout1.pdf",
        "Intelligent Addressable Fire Alarm System Loop & Riser Schematic",
        "Fire Alarm Schematic",
        (
            "FIRE ALARM SYSTEM ARCHITECTURE & INTEGRATION:\n"
            "1. Central Networked Fire Alarm Control Panel (FACP) with 8 Class-A Signaling Line Circuits (SLC) loops per EN 54 & NBC 2016.\n"
            "2. Addressable multi-sensor optical smoke and rate-of-rise heat detectors installed in all office zones, lobbies, and electrical shafts.\n"
            "3. Addressable manual pull stations (MCP) with transparent protective flip-covers positioned at every emergency exit doorway.\n"
            "4. Audio-visual strobe sounders delivering 100 dBA audio output with synchronized 75 candela xenon flashes.\n"
            "5. Interlock control modules wired for automatic tripping of AHUs, closing of fire smoke dampers, and grounding of elevators."
        ),
        {
            "headers": ["Loop ID", "Floor / Building Zone", "Detectors", "Manual Calls", "Control Modules", "Total Devices"],
            "rows": [
                ["Loop 1", "Ground Floor North Wing & Lobby", "84 Smoke / 12 Heat", "8 MCPs", "14 Modules", "118 Devices"],
                ["Loop 2", "Ground Floor South Wing & Portico", "78 Smoke / 10 Heat", "8 MCPs", "12 Modules", "108 Devices"],
                ["Loop 3", "First Floor Legislative Chambers", "96 Smoke / 16 Heat", "12 MCPs", "18 Modules", "142 Devices"],
                ["Loop 4", "Second Floor Cabinet & Ministers", "90 Smoke / 14 Heat", "10 MCPs", "16 Modules", "130 Devices"],
                ["Loop 5", "Basement Parking & Plant Rooms", "65 Heat / 20 Flame", "12 MCPs", "22 Modules", "119 Devices"]
            ],
            "widths": [60, 160, 110, 65, 75, 55]
        }
    ),
    (
        "SL-288-Amaravati-LA-PUBLIC ADDRESS SYSTEM SCHEMATIC DIAGRAM PA SCHEMATIC.pdf",
        "Public Address & Voice Alarm Emergency Riser Schematic",
        "PA & Voice Evacuation Schematic",
        (
            "PA & VOICE EVACUATION SYSTEM SPECIFICATIONS:\n"
            "1. Conforming to EN 54-16 standard with supervised amplifier channels and dual 1:1 standby auto-failover.\n"
            "2. Central digital signal processor (DSP) audio matrix controller with 16 audio input buses and 32 supervised output zones.\n"
            "3. Assembly Chamber and Dignitary Galleries equipped with 6W high-clarity flush ceiling speakers delivering STI > 0.65 speech intelligibility.\n"
            "4. Basement parking, plant rooms, and outdoor courtyards equipped with 15W IP66 weatherproof directional horn speakers.\n"
            "5. Priority 1 Fire Alarm override triggers pre-recorded phased evacuation messages in Telugu, English, and Hindi."
        ),
        {
            "headers": ["Audio Zone", "Coverage Area", "Speaker Type", "Unit Power", "Qty", "Total Power"],
            "rows": [
                ["Zone 01", "Main Assembly Chamber", "Ceiling Coaxial 6W", "6 Watts RMS", "48 Units", "288 Watts"],
                ["Zone 02", "Speaker's Gallery & Press", "Ceiling Coaxial 6W", "6 Watts RMS", "24 Units", "144 Watts"],
                ["Zone 03", "VVIP Corridors & Lobbies", "Ceiling Flush 6W", "6 Watts RMS", "36 Units", "216 Watts"],
                ["Zone 04", "Basement Parking Level -1", "Re-entrant Horn 15W", "15 Watts RMS", "20 Units", "300 Watts"],
                ["Zone 05", "Basement Parking Level -2", "Re-entrant Horn 15W", "15 Watts RMS", "20 Units", "300 Watts"]
            ],
            "widths": [60, 150, 110, 75, 50, 60]
        }
    ),
    (
        "SL-288- SINGLE LINE SCHEMATIC DIAGRAM - AHU PANEL AHU PANEL-1-3.pdf",
        "Air Handling Unit (AHU) Motor Control Center Starter Schematic",
        "HVAC Electrical Schematic",
        (
            "AHU MOTOR STARTER PANEL DESIGN & CONTROL INTERLOCKS:\n"
            "1. Fully compartmentalized Form 3b motor control center (MCC) housing starters for AHU-01 through AHU-08.\n"
            "2. Variable Frequency Drives (VFD) equipped with bypass contactors, EMC line filters, and Modbus communication cards.\n"
            "3. Microprocessor motor protection relays providing thermal overload, single phasing, locked rotor, and earth leakage protection.\n"
            "4. Safety Interlock 1: Differential pressure switch across supply fan proving airflow before electric heating or cooling is energized.\n"
            "5. Safety Interlock 2: High static pressure safety cut-out switch opening control circuit if duct static exceeds 750 Pa.\n"
            "6. Safety Interlock 3: Hardwired dry contact from Fire Alarm Panel immediately opening main contactor upon fire alarm trip."
        ),
        {
            "headers": ["Starter Tag", "AHU Served", "Motor Rating", "Full Load Amps", "VFD Model", "MCCB Rating"],
            "rows": [
                ["STR-01", "AHU-01 (Assembly Hall North)", "22.0 kW (30 HP)", "42.0 Amps", "Danfoss FC-102", "63A 3P 36kA"],
                ["STR-02", "AHU-02 (Assembly Hall South)", "22.0 kW (30 HP)", "42.0 Amps", "Danfoss FC-102", "63A 3P 36kA"],
                ["STR-03", "AHU-03 (Speaker Secretariat)", "15.0 kW (20 HP)", "29.0 Amps", "Danfoss FC-102", "40A 3P 36kA"],
                ["STR-04", "AHU-04 (Cabinet Room)", "15.0 kW (20 HP)", "29.0 Amps", "Danfoss FC-102", "40A 3P 36kA"],
                ["STR-05", "AHU-05 (Press & Media Hall)", "11.0 kW (15 HP)", "21.5 Amps", "Danfoss FC-102", "32A 3P 25kA"]
            ],
            "widths": [65, 140, 85, 75, 85, 55]
        }
    ),
    (
        "SL-288 _ AMARAVATI ASSEMBLY SCHEMATIC DIAGRAM - TERTIARY CHILLED WATER PUMP PANE...pdf",
        "Tertiary Chilled Water Pump Control Panel Schematic",
        "Chilled Water Pumping Schematic",
        (
            "CHILLED WATER CIRCULATION SCHEMATIC & DIFFERENTIAL PRESSURE CONTROL:\n"
            "1. Secondary & Tertiary chilled water circuit operating at 6.7°C supply / 13.3°C return temperature (Delta T = 6.6°C).\n"
            "2. Variable primary and secondary pumping scheme utilizing end-suction centrifugal pumps with IE4 permanent magnet motors.\n"
            "3. Differential pressure transmitter located at hydraulically most remote AHU coil modulating pump speed to maintain 1.8 bar DP.\n"
            "4. Automatic equalized run-time rotation: System swaps duty and standby pumps every 168 operating hours.\n"
            "5. High accuracy electromagnetic flow meter and paired PT1000 temperature sensors transmitting BTU cooling data to Central BMS."
        ),
        {
            "headers": ["Pump ID", "Service Designation", "Flow Rate", "Head", "Motor kW", "Impeller Material"],
            "rows": [
                ["PMP-CHW-01", "Primary CHW Pump (Duty 1)", "350 m3/hr", "22 Metres", "37 kW IE4", "SS 316 Stainless Steel"],
                ["PMP-CHW-02", "Primary CHW Pump (Duty 2)", "350 m3/hr", "22 Metres", "37 kW IE4", "SS 316 Stainless Steel"],
                ["PMP-CHW-03", "Primary CHW Pump (Standby)", "350 m3/hr", "22 Metres", "37 kW IE4", "SS 316 Stainless Steel"],
                ["PMP-SEC-01", "Secondary CHW Pump (Duty 1)", "420 m3/hr", "38 Metres", "55 kW IE4", "SS 316 Stainless Steel"],
                ["PMP-SEC-02", "Secondary CHW Pump (Duty 2)", "420 m3/hr", "38 Metres", "55 kW IE4", "SS 316 Stainless Steel"],
                ["PMP-SEC-03", "Secondary CHW Pump (Standby)", "420 m3/hr", "38 Metres", "55 kW IE4", "SS 316 Stainless Steel"]
            ],
            "widths": [80, 130, 70, 60, 65, 100]
        }
    ),
    (
        "SL-288-WS-99.pdf",
        "Water Supply Treatment Plant & Hydro-Pneumatic Booster Layout",
        "Water Treatment & Plumbing Schematic",
        (
            "POTABLE WATER TREATMENT & PRESSURIZED DISTRIBUTION SCHEMATIC:\n"
            "1. Raw water storage capacity: 500,000 Litres underground RCC reservoir with food-grade epoxy coating.\n"
            "2. Central filtration train: 2x 75 m3/hr Multi-Grade Sand Filters (MGF) followed by 2x Activated Carbon Filters (ACF).\n"
            "3. Drinking water Reverse Osmosis (RO) system: 50 KLD capacity with 2:1 staging, cartridge pre-filters, and UV disinfection.\n"
            "4. Hydro-Pneumatic Pumping Skid: 3x vertical multistage centrifugal pumps (2 Working + 1 Standby) operating on constant pressure control.\n"
            "5. Pre-charged nitrogen diaphragm expansion tank (500L) dampening hydraulic surges and cycling pulses across terminal fixtures."
        ),
        {
            "headers": ["Equipment Tag", "Equipment Description", "Capacity", "Operating Pressure", "Motor Rating", "MOC"],
            "rows": [
                ["MGF-01/02", "Multi-Grade Sand Filters", "75 m3/hr each", "3.5 bar", "N/A (Pressure Vessel)", "FRP / MS Epoxy Lined"],
                ["ACF-01/02", "Activated Carbon Filters", "75 m3/hr each", "3.5 bar", "N/A (Pressure Vessel)", "FRP / MS Epoxy Lined"],
                ["RO-SKID", "Reverse Osmosis Membrane Unit", "50 KLD", "14.0 bar", "11.0 kW HP Pump", "SS 316 High Pressure"],
                ["HYPN-PMP-01", "Booster Pump 1 (Duty)", "45 m3/hr", "4.5 bar", "7.5 kW Vertical Multi", "SS 304 Stainless Steel"],
                ["HYPN-PMP-02", "Booster Pump 2 (Duty)", "45 m3/hr", "4.5 bar", "7.5 kW Vertical Multi", "SS 304 Stainless Steel"],
                ["HYPN-PMP-03", "Booster Pump 3 (Standby)", "45 m3/hr", "4.5 bar", "7.5 kW Vertical Multi", "SS 304 Stainless Steel"]
            ],
            "widths": [80, 130, 65, 75, 80, 75]
        }
    ),
    (
        "SL-288-DRF-101.pdf",
        "Basement MEP Plant Room Floor Drainage & Sump Pump Detail",
        "Drainage & Sump Detail Drawing",
        (
            "PLANT ROOM DRAINAGE & SUBMERSIBLE DEWATERING DETAIL:\n"
            "1. Perimeter floor drainage trenches in Chiller room, Boiler room, Substation, and DG yard with heavy-duty ductile iron gratings.\n"
            "2. Sump pit construction: 3500 x 3000 x 2800 mm deep reinforced concrete pit with crystalline waterproofing compound.\n"
            "3. Dewatering pump set: Dual submersible non-clog cutter pumps (1 Duty + 1 Standby) each rated for 50 m3/hr @ 18m head.\n"
            "4. Pump impeller designed to pass solid spherical debris up to 50mm diameter without clogging.\n"
            "5. Automated 4-float level switch arrangement: Low Cut-off, Lead Pump Start, Lag Pump Start (High Inflow), and Critical High Alarm."
        ),
        {
            "headers": ["Sump Pit Tag", "Location / Area", "Pit Dimensions", "Discharge Pump", "Flow Rate", "Discharge Line"],
            "rows": [
                ["SUMP-01", "Chiller Plant Room", "3.5 x 3.0 x 2.8m", "Dual Submersible 5.5 kW", "50 m3/hr @ 18m", "100mm CI Pipe"],
                ["SUMP-02", "Main Substation Trench", "2.5 x 2.0 x 2.2m", "Dual Submersible 3.7 kW", "30 m3/hr @ 15m", "80mm CI Pipe"],
                ["SUMP-03", "DG Fuel Tank Yard", "2.0 x 2.0 x 2.0m", "Flameproof Submersible 2.2 kW", "15 m3/hr @ 12m", "65mm GI Pipe"],
                ["SUMP-04", "Fire Pump Room", "3.0 x 2.5 x 2.5m", "Dual Submersible 5.5 kW", "50 m3/hr @ 18m", "100mm CI Pipe"]
            ],
            "widths": [70, 120, 85, 115, 65, 50]
        }
    ),
    (
        "SL-288-DRF-101A.pdf",
        "Domestic & Flushing Water Supply Riser Diagram",
        "Water Supply Riser Diagram",
        (
            "DOMESTIC & FLUSHING WATER DISTRIBUTION RISER SPECIFICATIONS:\n"
            "1. Dual-pipe distribution system separating potable domestic water from treated recycled flushing water per NBC 2016.\n"
            "2. Potable Water Riser: CPVC SDR-11 piping conforming to ASTM D2846 with solvent weld joints tested to 15 kg/cm2.\n"
            "3. Flushing Water Riser: UPVC Class-3 piping conforming to IS 4985 with heavy-duty solvent cement joints.\n"
            "4. Pressure regulating valve (PRV) stations installed on each floor branch to ensure terminal fixture pressure between 2.0 and 2.5 bar.\n"
            "5. Automatic air release valves (ARV) provided at top of each vertical riser to purge air pockets and avoid water hammer."
        ),
        {
            "headers": ["Riser Tag", "Service", "Levels Served", "Riser Diameter", "Design Flow", "PRV Setting"],
            "rows": [
                ["RSR-DOM-01", "Potable Water", "Basement to Level 4 (West)", "65mm CPVC", "12.5 m3/hr", "2.2 bar"],
                ["RSR-DOM-02", "Potable Water", "Basement to Level 4 (East)", "65mm CPVC", "12.5 m3/hr", "2.2 bar"],
                ["RSR-DOM-03", "Potable Water", "Legislative Assembly Core", "80mm CPVC", "18.0 m3/hr", "2.5 bar"],
                ["RSR-FLU-01", "Flushing Recycled", "Basement to Level 4 (West)", "80mm UPVC", "16.0 m3/hr", "2.0 bar"],
                ["RSR-FLU-02", "Flushing Recycled", "Basement to Level 4 (East)", "80mm UPVC", "16.0 m3/hr", "2.0 bar"],
                ["RSR-FLU-03", "Flushing Recycled", "Legislative Assembly Core", "100mm UPVC", "24.0 m3/hr", "2.2 bar"]
            ],
            "widths": [70, 95, 125, 75, 70, 70]
        }
    ),
    (
        "SL-288 -CHW TYPE AHU DATA SHEET _ 15.11.2025 - Copy.pdf",
        "Chilled Water Double-Skin Air Handling Unit Technical Data Sheet",
        "AHU Engineering Data Sheet",
        (
            "DOUBLE SKIN CHW AIR HANDLING UNIT ENGINEERING DATA SHEET:\n"
            "1. Thermal break extruded aluminum framework with 50mm injected polyurethane foam (PUF) insulation panels (Density 40 kg/m3).\n"
            "2. Double skin casing: Outer skin 0.8mm pre-coated GI sheet; Inner skin 0.8mm plain GI with antimicrobial powder coating.\n"
            "3. Plug fan: Direct-drive backward curved aerofoil impeller dynamically balanced to ISO 1940 Grade G2.5 with IE4 synchronous motor.\n"
            "4. Cooling coil: 6-row deep copper tube (12.7mm OD) with hydrophilic coated corrugated aluminum fins (12 fins per inch).\n"
            "5. Dual filtration: Pre-filter MERV 8 (10 Micron, G4) followed by fine secondary bag filter MERV 13 (2.5 Micron, F7)."
        ),
        {
            "headers": ["Parameter", "AHU-01 (Chamber)", "AHU-02 (Cabinet)", "AHU-03 (Lobby)", "AHU-04 (Press Hall)"],
            "rows": [
                ["Airflow Capacity", "18,000 CFM", "12,000 CFM", "15,000 CFM", "10,000 CFM"],
                ["External Static Pressure", "450 Pa", "400 Pa", "400 Pa", "350 Pa"],
                ["Cooling Capacity", "92.0 TR", "61.5 TR", "76.8 TR", "51.2 TR"],
                ["Water Flow Rate", "220 USGPM", "148 USGPM", "184 USGPM", "123 USGPM"],
                ["Entering Water Temp", "6.7°C (44°F)", "6.7°C (44°F)", "6.7°C (44°F)", "6.7°C (44°F)"],
                ["Leaving Water Temp", "13.3°C (56°F)", "13.3°C (56°F)", "13.3°C (56°F)", "13.3°C (56°F)"],
                ["Motor Rating", "22.0 kW (IE4)", "15.0 kW (IE4)", "18.5 kW (IE4)", "11.0 kW (IE4)"]
            ],
            "widths": [115, 95, 95, 95, 105]
        }
    ),
    (
        "SL-288 -DX TYPE AHU DATA SHEET _ 15.11.2025 - Copy.pdf",
        "Direct Expansion (DX) Precision Air Conditioning Technical Data Sheet",
        "Precision AC Data Sheet",
        (
            "PRECISION AIR CONDITIONING (PAC) DATA SHEET FOR DATA CENTER & BROADCASTING:\n"
            "1. Inverter scroll compressor with variable speed modulation and eco-friendly R-410A refrigerant.\n"
            "2. Sensible Heat Ratio (SHR) >= 0.95 specifically engineered for high sensible heat loads generated by IT server racks.\n"
            "3. Precision temperature regulation (+/- 1.0°C) and relative humidity regulation (+/- 5.0% RH) via integrated microprocessors.\n"
            "4. Modulating electronic expansion valve (EEV) adjusting refrigerant mass flow instantaneously based on thermal load.\n"
            "5. Electrode steam humidifier with stainless steel electrodes and automatic water drainage purge cycles."
        ),
        {
            "headers": ["Unit Model Tag", "Location Served", "Total kW", "Sensible kW", "Airflow CFM", "Refrigerant"],
            "rows": [
                ["PAC-01 (Duty)", "Assembly Data Center 1", "68.0 kW", "65.0 kW", "9,500 CFM", "R-410A Inverter"],
                ["PAC-02 (Standby)", "Assembly Data Center 1", "68.0 kW", "65.0 kW", "9,500 CFM", "R-410A Inverter"],
                ["PAC-03 (Duty)", "Broadcasting Control Room", "42.0 kW", "40.0 kW", "6,200 CFM", "R-410A Inverter"],
                ["PAC-04 (Standby)", "Broadcasting Control Room", "42.0 kW", "40.0 kW", "6,200 CFM", "R-410A Inverter"],
                ["PAC-05 (Duty)", "UPS & Battery Room", "35.0 kW", "34.0 kW", "5,400 CFM", "R-410A Inverter"]
            ],
            "widths": [85, 130, 60, 65, 75, 90]
        }
    ),
    (
        "SL-288 - Heat Recovery data sheet_15.11.2025.pdf",
        "Rotary Energy Recovery Enthalpy Wheel Technical Data Sheet",
        "Energy Recovery Wheel Data Sheet",
        (
            "ENERGY RECOVERY WHEEL (ERV) PERFORMANCE SPECIFICATIONS:\n"
            "1. Conforming to ASHRAE 84 and Eurovent certified for sensible and latent energy exchange between exhaust and fresh air.\n"
            "2. Aluminum honeycomb wheel rotor with polymer coating impregnated with 3A molecular sieve desiccant.\n"
            "3. Desiccant pore diameter of 3 Angstroms selectively captures water vapor while repelling organic pollutants and smells.\n"
            "4. Built-in purge angle sector preventing cross-contamination: Cross-leakage strictly < 0.04% of total air volume.\n"
            "5. Stepper motor variable speed drive with microprocessor controller for automatic freeze protection in winter conditions."
        ),
        {
            "headers": ["Wheel Tag", "Fresh Air m3/h", "Exhaust Air m3/h", "Sensible Eff %", "Latent Eff %", "Power kW Saved"],
            "rows": [
                ["HRW-01 (Chamber)", "15,000 m3/h", "15,000 m3/h", "77.5%", "72.0%", "54.2 kW"],
                ["HRW-02 (Secretariat)", "10,000 m3/h", "10,000 m3/h", "76.0%", "70.5%", "35.8 kW"],
                ["HRW-03 (Ministers Block)", "12,000 m3/h", "12,000 m3/h", "78.0%", "73.0%", "44.0 kW"],
                ["HRW-04 (Press & Media)", "8,000 m3/h", "8,000 m3/h", "75.5%", "71.0%", "28.5 kW"]
            ],
            "widths": [100, 80, 80, 75, 75, 95]
        }
    ),
    (
        "SL-288 - VENTILATION - FRESH AIR FAN FOR KITCHEN DATA SHEET _15.11.2025.pdf",
        "Kitchen Fresh Air Supply Axial Fan Technical Data Sheet",
        "Kitchen Supply Fan Data Sheet",
        (
            "KITCHEN FRESH AIR MAKE-UP AXIAL FAN SPECIFICATIONS:\n"
            "1. Tube axial flow supply fan with aerofoil adjustable pitch die-cast aluminum blades.\n"
            "2. Heavy gauge hot-dip galvanized casing with flanged connections to SMACNA rectangular supply air ductwork.\n"
            "3. Totally Enclosed Fan Cooled (TEFC) Class H insulated motor rated for continuous operation at 55°C ambient.\n"
            "4. Washable aluminum synthetic pre-filter MERV 8 integrated at weather louvre intake.\n"
            "5. Sound attenuator section reducing fan breakout sound to <= 62 dBA at 1.5m perimeter distance."
        ),
        {
            "headers": ["Fan Tag", "Location Served", "Air Flow CFM", "Static Pressure", "Fan RPM", "Motor kW"],
            "rows": [
                ["FAF-KIT-01", "Main Assembly Kitchen (Cooking Area)", "8,500 CFM", "350 Pa", "1440 RPM", "7.5 kW"],
                ["FAF-KIT-02", "Dignitary Dining Pantry Prep", "4,200 CFM", "280 Pa", "1440 RPM", "3.7 kW"],
                ["FAF-KIT-03", "Staff Cafeteria Kitchen", "6,000 CFM", "320 Pa", "1440 RPM", "5.5 kW"]
            ],
            "widths": [85, 160, 75, 75, 55, 55]
        }
    ),
    (
        "SL-288 - VENTILATION - KITCHEN DRY SCRUBBER & FAN DATA SHEET - 15.11.2025.pdf",
        "Kitchen Electrostatic Precipitator (ESP) Grease Scrubber Data Sheet",
        "Kitchen Scrubber Data Sheet",
        (
            "COMMERCIAL KITCHEN EXHAUST SCRUBBER & CENTRIFUGAL FAN DATA:\n"
            "1. Two-stage Electrostatic Precipitator (ESP) ionizing cell with certified grease extraction efficiency >= 95%.\n"
            "2. Integrated high-output UV-C ozone sterilization lamps destroying residual volatile grease vapors and odors.\n"
            "3. Fire-rated high-temperature backward curved centrifugal exhaust fan rated for 400°C / 2 hours continuous run per EN 12101-3.\n"
            "4. Automated wash cycle with hot water and eco-detergent sprays purging collected grease to grease interceptor trap.\n"
            "5. Fire suppression interlock with Ansul R-102 wet chemical kitchen hood system."
        ),
        {
            "headers": ["Scrubber Tag", "Exhaust CFM", "ESP Cell Qty", "UV-C Lamps", "Exhaust Fan Motor", "Fire Rating"],
            "rows": [
                ["ESP-SCR-01", "9,000 CFM", "6 Dual Cells", "12x 150W UV-C", "11.0 kW Centrifugal", "400°C / 2 Hrs"],
                ["ESP-SCR-02", "4,500 CFM", "3 Dual Cells", "6x 150W UV-C", "5.5 kW Centrifugal", "400°C / 2 Hrs"],
                ["ESP-SCR-03", "6,500 CFM", "4 Dual Cells", "8x 150W UV-C", "7.5 kW Centrifugal", "400°C / 2 Hrs"]
            ],
            "widths": [80, 80, 75, 80, 110, 80]
        }
    ),
    (
        "SL-288 - VENTILATION FAN -HVAC DATA SHEET __.pdf",
        "Restroom & Core Exhaust In-Line Centrifugal Fans Data Sheet",
        "Ventilation Fan Data Sheet",
        (
            "IN-LINE CABINET CENTRIFUGAL EXHAUST FAN DATA SHEET:\n"
            "1. Acoustic insulated double-walled cabinet with backward-curved high-efficiency centrifugal impeller.\n"
            "2. Sound absorption lining: 25mm high-density acoustic fiberglass blanket achieving quiet operational noise <= 48 dBA.\n"
            "3. High-efficiency IP55 dust and moisture sealed motor with self-resetting thermal cut-out protection.\n"
            "4. Built-in gravity back-draft damper preventing cold air or odor back-flow when unit is powered off.\n"
            "5. Modulating speed control integrated with restroom occupancy sensors for energy conservation."
        ),
        {
            "headers": ["Fan Tag", "Exhaust Zone", "Flow m3/h", "Static Pa", "Noise dBA", "Motor Wattage"],
            "rows": [
                ["EF-TOI-01", "VVIP Dignitary Restrooms L1", "1,800 m3/h", "220 Pa", "42 dBA", "380 Watts"],
                ["EF-TOI-02", "General Assembly Restrooms L1", "3,200 m3/h", "260 Pa", "46 dBA", "650 Watts"],
                ["EF-TOI-03", "Press & Media Restrooms L2", "2,400 m3/h", "240 Pa", "44 dBA", "480 Watts"],
                ["EF-ELEC-01", "Substation Battery Exhaust", "1,500 m3/h (Flameproof)", "200 Pa", "48 dBA", "550 Watts (Ex-d)"]
            ],
            "widths": [75, 150, 75, 65, 65, 75]
        }
    ),
    (
        "SL-288- PUMP DATA SHEET ASSEMBLY AMARAVATI.pdf",
        "Primary & Secondary Chilled Water Pumps Technical Data Sheet",
        "Chilled Water Pump Data Sheet",
        (
            "PRIMARY & SECONDARY CENTRIFUGAL PUMP TECHNICAL DATA SHEET:\n"
            "1. Horizontal split-case and end-suction centrifugal pumps engineered for continuous duty in district cooling applications.\n"
            "2. Pump casing: High-grade cast iron (ASTM A48 Class 35); Impeller: Machined nickel-aluminum bronze (ASTM B148).\n"
            "3. Heavy-duty silicon carbide vs silicon carbide mechanical face seals with EPDM O-rings suitable for glycol solution.\n"
            "4. Electric motors: IE4 super-premium efficiency squirrel cage induction motors conforming to IEC 60034-30-1.\n"
            "5. Factory hydrostatically tested to 1.5 times the maximum working pressure (Tested to 24 bar for 30 minutes)."
        ),
        {
            "headers": ["Pump Model", "Service", "Flow m3/hr", "Head m", "Impeller Dia", "Efficiency %", "Motor kW"],
            "rows": [
                ["NK 125-250", "Primary Chiller Evaporator", "350 m3/h", "22 m", "254 mm", "84.5%", "30 kW IE4"],
                ["NK 150-315", "Secondary Distribution", "420 m3/h", "38 m", "312 mm", "86.2%", "55 kW IE4"],
                ["NK 100-200", "Condenser Cooling Tower", "480 m3/h", "25 m", "215 mm", "85.0%", "45 kW IE4"],
                ["CRN 32-4", "Chilled Water Pressurization", "25 m3/h", "45 m", "Multi", "78.0%", "5.5 kW IE4"]
            ],
            "widths": [75, 125, 65, 50, 65, 65, 60]
        }
    ),
    (
        "SL-288 - SINGLE LINE SCHEMATIC DIAGRAM - VENTILATION PANELS VENTILATION PANELS.pdf",
        "Basement Smoke Extraction & Pressurization Panel Electrical SLD",
        "Ventilation Electrical Schematic",
        (
            "SMOKE EXTRACTION & STAIRCASE PRESSURIZATION ELECTRICAL PANEL SLD:\n"
            "1. Dual redundant power supply with automatic transfer switch (ATS) complying with NFPA 92 and NBC 2016.\n"
            "2. Fire rated electrical switchboard with 2-hour fire endurance rating (CWZ per BS 6387) for emergency smoke fan operation.\n"
            "3. Dual speed starters (Star-Delta / Pole Changing) providing low speed for normal ventilation and high speed for fire smoke purge.\n"
            "4. Manual override firefighter control panel (FFCP) located in the Central Fire Command Center.\n"
            "5. Auto-activation upon duct smoke detector or sprinkler water flow switch confirmation."
        ),
        {
            "headers": ["Fan Feeder", "Service / Location", "Normal Speed kW", "Emergency Smoke kW", "Starter Type", "Cable Type"],
            "rows": [
                ["F-SMK-01", "Basement -1 Smoke Extract", "11.0 kW (Low)", "30.0 kW (High)", "Dual Speed Star-Delta", "Fire Survival 4C x 25"],
                ["F-SMK-02", "Basement -2 Smoke Extract", "11.0 kW (Low)", "30.0 kW (High)", "Dual Speed Star-Delta", "Fire Survival 4C x 25"],
                ["F-PRS-01", "Staircase 1 Pressurization", "N/A", "15.0 kW (Full)", "Star-Delta Starter", "Fire Survival 4C x 16"],
                ["F-PRS-02", "Staircase 2 Pressurization", "N/A", "15.0 kW (Full)", "Star-Delta Starter", "Fire Survival 4C x 16"],
                ["F-LOB-01", "Fire Lift Lobby Pressurization", "N/A", "11.0 kW (Full)", "Direct On-Line (DOL)", "Fire Survival 4C x 10"]
            ],
            "widths": [65, 140, 75, 80, 85, 60]
        }
    ),
    (
        "SL-288 _ AMARAVATI ASSEMBLY SCHEMATIC DIAGRAM - TERTIARY CHILLED WATER PUMP PANE TERTIARY CHILLED WATER PUMP PANEL.pdf",
        "Chilled Water Tertiary Pump Starter & Modulation Control Schematic",
        "HVAC Tertiary Pump Schematic",
        (
            "TERTIARY CHW MOTOR STARTER & BMS INTERFACE SCHEMATIC:\n"
            "1. Three-pump variable speed manifold supplying chilled water to Assembly Hall and Cabinet high-comfort zones.\n"
            "2. Closed-loop PID controller taking input from two differential pressure sensors placed at the ends of supply loops.\n"
            "3. Microprocessor VFD drives with harmonic mitigation chokes keeping total harmonic distortion (THDi) < 3%.\n"
            "4. Hardwired interlock with motorized 2-way modulating control valves on terminal AHUs.\n"
            "5. Thermal overload and phase angle monitoring triggering instant standby pump start in less than 2.5 seconds."
        ),
        {
            "headers": ["Pump Unit", "Flow Capacity", "Head Metres", "Motor Rating", "Inverter Drive", "MCCB Protection"],
            "rows": [
                ["PMP-TER-01 (Duty)", "180 m3/hr", "32 Metres", "22.0 kW IE4", "ABB ACH580 VFD", "63A 3P 36kA"],
                ["PMP-TER-02 (Duty)", "180 m3/hr", "32 Metres", "22.0 kW IE4", "ABB ACH580 VFD", "63A 3P 36kA"],
                ["PMP-TER-03 (Standby)", "180 m3/hr", "32 Metres", "22.0 kW IE4", "ABB ACH580 VFD", "63A 3P 36kA"]
            ],
            "widths": [90, 85, 75, 80, 95, 80]
        }
    ),
    (
        "SL-288-EL0-057 - SINGLE LINE SCHEMATIC DIAGRAM - FIRE FIGHTING ELECTRICAL PANEL FF.pdf",
        "Fire Hydrant, Sprinkler & Jockey Pump Control Panel Electrical SLD",
        "Fire Pump Electrical Schematic",
        (
            "FIRE FIGHTING PUMP CONTROLLER ELECTRICAL SCHEMATIC & NFPA 20 CONFORMANCE:\n"
            "1. Automatic fire pump motor controller panel complying with NFPA 20 and IS 15301 standards.\n"
            "2. Dual incoming power supplies: Normal utility feed from Substation + Standby feeder from Emergency DG with mechanical interlock.\n"
            "3. Main Fire Pump (75 kW): Star-Delta starter with locked rotor over-current protection bypassed during emergency fire run.\n"
            "4. Jockey Pump (15 kW): DOL starter with adjustable pressure switch set-points (Cut-in: 6.0 kg/cm2, Cut-out: 7.5 kg/cm2).\n"
            "5. Diesel Engine Driven Standby Pump: Dual 24V DC battery sets with automatic float/boost chargers and solenoid starting valves."
        ),
        {
            "headers": ["Equipment Tag", "Equipment Name", "Capacity", "Head", "Starter / Drive", "Feeder Cable"],
            "rows": [
                ["FP-ELEC-01", "Main Electric Fire Pump", "2850 LPM", "88 Metres", "75 kW Star-Delta", "3.5C x 185 sq.mm FS"],
                ["FP-DSL-01", "Standby Diesel Engine Pump", "2850 LPM", "88 Metres", "95 HP 6-Cyl Diesel", "24V Dual Batteries"],
                ["FP-JCK-01", "System Jockey Pump", "180 LPM", "90 Metres", "15 kW DOL Starter", "3.5C x 25 sq.mm FS"],
                ["FP-SPR-01", "Main Sprinkler Electric Pump", "2850 LPM", "88 Metres", "75 kW Star-Delta", "3.5C x 185 sq.mm FS"]
            ],
            "widths": [75, 140, 70, 60, 95, 65]
        }
    ),
    (
        "SL-096B-EL0-058 - SINGLE LINE SCHEMATIC DIAGRAM - PLUMBING PANEL PHE SCHEMATIC.pdf",
        "Hydro-Pneumatic Booster & Submersible Sewage Panel Electrical SLD",
        "PHE Electrical Schematic",
        (
            "PUBLIC HEALTH ENGINEERING (PHE) MOTOR CONTROL PANEL SLD:\n"
            "1. Modular motor control center powering Hydro-Pneumatic booster pumps, WTP pumps, and basement sewage dewatering pumps.\n"
            "2. VFD master-slave booster pump control sequencing 3x 7.5 kW multistage vertical pumps based on 4-20mA pressure feedback.\n"
            "3. Dry run protection interlocked with capacitance level sensors in 500 KL underground water storage reservoir.\n"
            "4. Sewage submersible pump controller with automated alternation and auto-start of lag pump upon storm deluge.\n"
            "5. Remote monitoring signals (Pump Run, Trip, Water Level Alarms) wired to Central BMS."
        ),
        {
            "headers": ["PHE Pump Tag", "Service Purpose", "Motor kW", "Starter Type", "Full Load Amps", "MCCB Rating"],
            "rows": [
                ["PMP-HYP-01", "Domestic Booster Pump 1", "7.5 kW", "ABB ACS310 VFD", "15.2 Amps", "25A 3P 25kA"],
                ["PMP-HYP-02", "Domestic Booster Pump 2", "7.5 kW", "ABB ACS310 VFD", "15.2 Amps", "25A 3P 25kA"],
                ["PMP-HYP-03", "Domestic Booster Pump 3", "7.5 kW", "ABB ACS310 VFD", "15.2 Amps", "25A 3P 25kA"],
                ["PMP-SEW-01", "Basement Sewage Cutter 1", "5.5 kW", "Direct On-Line (DOL)", "11.5 Amps", "20A 3P 25kA"],
                ["PMP-SEW-02", "Basement Sewage Cutter 2", "5.5 kW", "Direct On-Line (DOL)", "11.5 Amps", "20A 3P 25kA"]
            ],
            "widths": [75, 135, 60, 95, 75, 65]
        }
    ),
    (
        "Assembly, Amaravati. - MEP DBR - R1.pdf",
        "Amaravati Legislative Assembly Complex MEP Design Basis Report",
        "MEP Design Basis Report",
        (
            "COMPREHENSIVE MEP DESIGN BASIS REPORT (DBR) — SUPER BLOCK E:\n"
            "1. METEOROLOGICAL DESIGN CONDITIONS (AMARAVATI CAPITAL REGION):\n"
            "   • Summer Design Ambient: 44.0°C Dry Bulb / 28.0°C Wet Bulb; Daily Range: 12.0°C.\n"
            "   • Monsoon Design Ambient: 34.0°C Dry Bulb / 29.0°C Wet Bulb.\n"
            "   • Indoor Design Conditions: 23.5°C +/- 1.0°C Dry Bulb; 55% +/- 5% Relative Humidity.\n"
            "2. COOLING LOAD ESTIMATION:\n"
            "   • Total conditioned gross floor area: 68,500 m2 across Assembly Hall, Council Hall, Secretariats, and Courtyards.\n"
            "   • Total estimated block cooling load: 3,200 TR (Including 15% safety factor and fresh air enthalpy recovery).\n"
            "3. ELECTRICAL CONNECTED LOAD & DEMAND:\n"
            "   • Total connected electrical load: 5,500 kVA; Anticipated maximum demand: 4,100 kVA (Diversity factor = 0.75).\n"
            "   • Backup power requirement: 100% emergency standby back-up via 2x 1500 kVA + 1x 1000 kVA DG sets.\n"
            "4. WATER SUPPLY & SUSTAINABILITY (GRIHA 5-STAR TARGET):\n"
            "   • Total water requirement: 220 KLD; Fresh potable water: 95 KLD; Recycled treated sewage water for flushing/HVAC: 125 KLD."
        ),
        {
            "headers": ["Building Sector", "Conditioned Area m2", "Cooling Load TR", "Power kVA", "Water Demand KLD"],
            "rows": [
                ["Sector A: Legislative Chamber", "18,500 m2", "980 TR", "1,650 kVA", "65 KLD"],
                ["Sector B: Council Chamber", "14,200 m2", "720 TR", "1,200 kVA", "45 KLD"],
                ["Sector C: Speaker & Cabinet", "16,800 m2", "780 TR", "1,350 kVA", "55 KLD"],
                ["Sector D: Media, Press & Visitors", "19,000 m2", "720 TR", "1,300 kVA", "55 KLD"],
                ["Total Complex Gross", "68,500 m2", "3,200 TR", "5,500 kVA", "220 KLD"]
            ],
            "widths": [140, 95, 85, 85, 100]
        }
    ),
    (
        "Design_Specification.pdf",
        "Amaravati Government Complex General Engineering Standards",
        "Design Specification Dossier",
        (
            "GENERAL ENGINEERING DESIGN STANDARDS & MATERIALS DOSSIER:\n"
            "1. CONCRETE & FOUNDATION ENGINEERING:\n"
            "   • Substructure concrete: Grade M40/M50 Self-Compacting Concrete (SCC) with microsilica for durability against soil sulfates.\n"
            "   • Reinforcing steel: High-yield strength deformed bars Fe 550D conforming to IS 1786 with minimum 16% elongation.\n"
            "2. STRUCTURAL STEELWORK SPECIFICATIONS:\n"
            "   • Structural steel hollow sections and built-up plate girders conforming to IS 2062 Grade E350BR / E410BR.\n"
            "   • All full-penetration butt welds subject to 100% Non-Destructive Testing (NDT) via Ultrasonic and Radiographic inspection.\n"
            "3. SEISMIC RESISTANCE & WIND RESISTANCE:\n"
            "   • Designed for Seismic Zone III with Zone Factor Z = 0.16 and Importance Factor I = 1.5 per IS 1893 (Part 1).\n"
            "   • Basic wind speed Vb = 50 m/s with terrain category 2 and cyclonic importance factor k4 = 1.15 per IS 875 (Part 3)."
        ),
        {
            "headers": ["Structural Element", "Concrete Grade", "Steel Grade", "Cover mm", "Exposure Class"],
            "rows": [
                ["Raft Foundation Slab", "M50 Self-Compacting", "Fe 550D TMT", "75 mm", "Severe (Soil Contact)"],
                ["Substructure Retaining Walls", "M45 Waterproofed", "Fe 550D TMT", "50 mm", "Severe (Soil Contact)"],
                ["Superstructure Mega Columns", "M60 High Strength", "Fe 550D TMT", "40 mm", "Moderate"],
                ["Post-Tensioned Floor Beams", "M50 Prestressed", "Fe 550D + Low Relax Strands", "35 mm", "Mild (Internal Air-con)"],
                ["Iconic Spire Tower Pylons", "M60 Composite Core", "Grade E410 Steel + Fe 550D", "50 mm", "Very Severe (Wind/Weather)"]
            ],
            "widths": [135, 95, 115, 60, 100]
        }
    ),
    (
        "Lift_D2E_VT Specification_Amravathi.pdf",
        "Vertical Transportation (Lifts & Escalators) Technical Specifications",
        "Elevator & Escalator Specs",
        (
            "HIGH-SPEED PASSENGER ELEVATORS & VERTICAL TRANSPORTATION SPECIFICATIONS:\n"
            "1. ELEVATOR MACHINES: Permanent Magnet Synchronous Motor (PMSM) gearless machine with regenerative VVVF drives.\n"
            "2. CAR SPEED & CAPACITY:\n"
            "   • VVIP Dignitary Elevators: Speed 2.5 m/s, capacity 20 passengers (1360 kg), center-opening stainless steel doors.\n"
            "   • Service & Stretcher Elevators: Speed 1.75 m/s, capacity 26 passengers (1768 kg), door clear opening 1200mm.\n"
            "3. DESTINATION CONTROL SYSTEM (DCS):\n"
            "   • Intelligent hall touch-screens assigning passengers to the optimal elevator car, minimizing travel time by 35%.\n"
            "4. SAFETY & EMERGENCY LIFE SUPPORT:\n"
            "   • Automatic Rescue Device (ARD) powered by maintenance-free sealed gel batteries bringing car to nearest landing during blackout.\n"
            "   • Firefighters lift compliance conforming to EN 81-72 with trap door, ladder, and waterproof electrical equipment."
        ),
        {
            "headers": ["Elevator Tag", "Service Purpose", "Capacity", "Speed", "Stops / Openings", "Car Dimensions (W x D)"],
            "rows": [
                ["LIFT-VVIP-01", "Hon'ble Speaker & CM Lift", "20 Pass (1360 kg)", "2.5 m/s", "6 Stops / 6 Openings", "2000 x 1750 mm"],
                ["LIFT-VVIP-02", "Ministers & Cabinet Lift", "20 Pass (1360 kg)", "2.5 m/s", "6 Stops / 6 Openings", "2000 x 1750 mm"],
                ["LIFT-PASS-01 to 04", "Members of Assembly (MLAs)", "20 Pass (1360 kg)", "2.0 m/s", "6 Stops / 6 Openings", "1900 x 1700 mm"],
                ["LIFT-SRV-01/02", "Service & Medical Stretcher", "26 Pass (1768 kg)", "1.75 m/s", "6 Stops / 6 Openings", "1600 x 2400 mm"],
                ["ESC-01 to 04", "Public Gallery Heavy Escalator", "9,000 Persons/hr", "0.5 m/s", "Rise: 6.5 Metres", "Step Width: 1000 mm"]
            ],
            "widths": [85, 125, 85, 55, 75, 80]
        }
    )
]

for dwg_fn, dwg_title, dwg_cat, dwg_text, dwg_table in distinct_drawings_996686:
    create_doc_pdf(
        DIR_996686 / dwg_fn,
        dwg_title,
        dwg_cat,
        t996686_meta,
        [
            {
                "section_title": dwg_title.upper(),
                "text": dwg_text,
                "table": dwg_table,
                "table_y": 550,
                "is_drawing": True,
                "dwg_no": dwg_fn.replace(".pdf", "")[:30]
            }
        ]
    )

print("\n>>> Re-packaging authentic DRAWINGS.zip for Tender 996686...")
drawings_zip_path = DIR_996686 / "DRAWINGS.zip"
with zipfile.ZipFile(drawings_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for dwg_fn, _, _, _, _ in distinct_drawings_996686:
        fpath = DIR_996686 / dwg_fn
        if fpath.exists():
            zf.write(fpath, arcname=dwg_fn)
print(f"  ✓ Rebuilt 'DRAWINGS.zip' ({drawings_zip_path.stat().st_size / 1024:.1f} KB, {len(distinct_drawings_996686)} authentic drawings)")

print("\n>>> Re-packaging authentic Tender_996686_All_Documents.zip...")
all_zip_996686 = DIR_996686 / "Tender_996686_All_Documents.zip"
with zipfile.ZipFile(all_zip_996686, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in DIR_996686.iterdir():
        if f.is_file() and f.name != all_zip_996686.name and not f.name.startswith("."):
            zf.write(f, arcname=f.name)
print(f"  ✓ Rebuilt 'Tender_996686_All_Documents.zip' ({all_zip_996686.stat().st_size / 1024:.1f} KB)")

print("\n>>> Successfully generated distinct authentic technical documents for all tenders!")
