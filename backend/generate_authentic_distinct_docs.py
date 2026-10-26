import os
import re
from pathlib import Path
import fitz  # PyMuPDF
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import zipfile

STORAGE_DIR = Path(__file__).resolve().parent / "storage" / "Andhra Pradesh" / "GIS"

def draw_cad_title_block(p, dwg_no, dwg_title, rev="R0", scale="1:100", date="28-09-2026"):
    """Draw an authentic engineering CAD title block in the bottom right corner."""
    # Outer frame
    p.draw_rect(fitz.Rect(30, 30, 565, 812), color=(0.1, 0.15, 0.3), width=1.5)
    p.draw_rect(fitz.Rect(32, 32, 563, 810), color=(0.1, 0.15, 0.3), width=0.5)
    
    # Title block box
    bx0, by0, bx1, by1 = 280, 710, 560, 808
    p.draw_rect(fitz.Rect(bx0, by0, bx1, by1), color=(0.1, 0.15, 0.3), fill=(0.97, 0.98, 1.0), width=1)
    p.draw_line(fitz.Point(bx0, by0 + 24), fitz.Point(bx1, by0 + 24), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(bx0, by0 + 48), fitz.Point(bx1, by0 + 48), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(bx0, by0 + 72), fitz.Point(bx1, by0 + 72), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(420, by0 + 48), fitz.Point(420, by1), color=(0.1, 0.15, 0.3), width=0.8)
    p.draw_line(fitz.Point(490, by0 + 48), fitz.Point(490, by1), color=(0.1, 0.15, 0.3), width=0.8)
    
    p.insert_text(fitz.Point(bx0 + 8, by0 + 16), "AMARAVATI GOVERNMENT COMPLEX — LEGISLATIVE ASSEMBLY", fontsize=8, fontname="helv", color=(0.08, 0.15, 0.4))
    p.insert_text(fitz.Point(bx0 + 8, by0 + 38), f"DWG TITLE: {dwg_title[:45]}", fontsize=8.5, fontname="helv", color=(0.1, 0.1, 0.1))
    p.insert_text(fitz.Point(bx0 + 8, by0 + 62), f"DRAWING NO: {dwg_no}", fontsize=8, fontname="helv", color=(0.08, 0.15, 0.4))
    p.insert_text(fitz.Point(426, by0 + 62), f"REV: {rev}", fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))
    p.insert_text(fitz.Point(496, by0 + 62), f"SCALE: {scale}", fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))
    p.insert_text(fitz.Point(bx0 + 8, by0 + 88), "CLIENT: AGICL / GOVT OF ANDHRA PRADESH", fontsize=7.5, fontname="helv", color=(0.3, 0.3, 0.3))
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
    total_pages = len(pages_data)
    
    for p_idx, page_info in enumerate(pages_data, 1):
        is_dwg = page_info.get("is_drawing", False)
        p = doc.new_page(width=595, height=842) # A4 portrait
        
        if is_dwg:
            # Drawing sheet view
            draw_cad_title_block(
                p, 
                dwg_no=page_info.get("dwg_no", out_path.stem),
                dwg_title=page_info.get("section_title", title),
                rev=page_info.get("rev", "R1"),
                scale=page_info.get("scale", "1:100")
            )
            # CAD layout header
            p.draw_rect(fitz.Rect(45, 45, 550, 75), color=(0.08, 0.15, 0.35), fill=(0.08, 0.15, 0.35))
            p.insert_text(fitz.Point(55, 62), "ANDHRA PRADESH STATE CAPITAL CITY INFRASTRUCTURE PROJECT", fontsize=9, fontname="helv", color=(1, 1, 1))
            p.insert_text(fitz.Point(55, 71), f"ENGINEERING WORKING DRAWING — TENDER REF #{t_id} (IFB: {t_no})", fontsize=7.5, fontname="helv", color=(0.85, 0.9, 1))
            
            # CAD schematic / notes
            body_text = page_info.get("text", "")
            if body_text:
                p.insert_textbox(fitz.Rect(45, 85, 550, 700), body_text, fontsize=8, fontname="helv", color=(0.1, 0.1, 0.1))
                
            # Draw schematic box grid
            p.draw_rect(fitz.Rect(45, 340, 270, 700), color=(0.6, 0.65, 0.75), fill=(0.98, 0.99, 1.0))
            p.insert_text(fitz.Point(52, 355), "STRUCTURAL COLUMN SCHEDULE & COORDINATE MATRIX", fontsize=8, fontname="helv", color=(0.08, 0.15, 0.35))
            cols = [
                ("Col C1-A", "M60 Grade", "1200x1200mm", "+18.50m Level"),
                ("Col C1-B", "M60 Grade", "1200x1200mm", "+18.50m Level"),
                ("Shear W1", "PT Flared", "800mm Thk", "+42.00m Level"),
                ("Spire Leg A", "Steel S355", "Dia 1600mm", "+120.0m Level"),
                ("Spire Leg B", "Steel S355", "Dia 1600mm", "+120.0m Level"),
                ("Spire Apex", "Aero Cone", "Dia 800mm", "+250.0m Level")
            ]
            cy = 370
            for c_name, c_mat, c_dim, c_lvl in cols:
                p.draw_line(fitz.Point(45, cy), fitz.Point(270, cy), color=(0.8, 0.85, 0.9))
                p.insert_text(fitz.Point(50, cy + 12), f"{c_name:<12} | {c_mat:<10} | {c_dim:<12} | {c_lvl}", fontsize=7, fontname="helv", color=(0.2, 0.2, 0.2))
                cy += 16
        else:
            # Header banner
            p.draw_rect(fitz.Rect(36, 36, 559, 90), color=(0.08, 0.15, 0.35), fill=(0.08, 0.15, 0.35))
            p.insert_text(fitz.Point(48, 54), "GOVERNMENT OF ANDHRA PRADESH", fontsize=11, fontname="helv", color=(1, 1, 1))
            p.insert_text(fitz.Point(48, 68), dept.upper()[:75], fontsize=8, fontname="helv", color=(0.85, 0.9, 1))
            p.insert_text(fitz.Point(48, 82), f"OFFICIAL PROCUREMENT DOSSIER — {doc_category.upper()}", fontsize=9, fontname="helv", color=(0.95, 0.8, 0.3))
            
            # Meta strip
            p.draw_rect(fitz.Rect(36, 96, 559, 142), color=(0.8, 0.85, 0.92), fill=(0.96, 0.98, 1.0))
            p.insert_text(fitz.Point(46, 110), f"Tender ID: {t_id}  |  Notice Ref: {t_no}", fontsize=8.5, fontname="helv", color=(0.08, 0.15, 0.35))
            p.insert_text(fitz.Point(46, 124), f"ECV: {ecv}  |  Closing Date: {due_date}", fontsize=8.5, fontname="helv", color=(0.2, 0.2, 0.2))
            p.insert_text(fitz.Point(46, 136), f"File: {out_path.name}", fontsize=8, fontname="helv", color=(0.35, 0.4, 0.5))
            
            # Section Title
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
                    bg = (0.97, 0.98, 1.0) if r_idx % 2 == 0 else (1.0, 1.0, 1.0)
                    p.draw_rect(fitz.Rect(36, cur_y, 559, cur_y + 16), color=(0.85, 0.88, 0.92), fill=bg)
                    cur_x = 36
                    for c_idx, cell in enumerate(row):
                        w = col_widths[c_idx]
                        p.insert_text(fitz.Point(cur_x + 4, cur_y + 11), str(cell)[:50], fontsize=7.5, fontname="helv", color=(0.15, 0.15, 0.15))
                        cur_x += w
                    cur_y += 16
            
            p.draw_line(fitz.Point(36, 800), fitz.Point(559, 800), color=(0.75, 0.75, 0.75), width=0.5)
            p.insert_text(fitz.Point(36, 814), f"Official e-Procurement Record | Tender ID #{t_id} | Ref: {t_no}", fontsize=7.5, fontname="helv", color=(0.4, 0.4, 0.4))
            p.insert_text(fitz.Point(490, 814), f"Page {p_idx} of {total_pages}", fontsize=7.5, fontname="helv", color=(0.4, 0.4, 0.4))
            
    doc.save(str(out_path))
    doc.close()
    print(f"  ✓ Saved '{out_path.name}' ({out_path.stat().st_size/1024:.1f} KB, {total_pages} pages)")


# -------------------------------------------------------------
# 1. GENERATE TENDER 1004936 COMPANION PDF FOR WORD DOC
# -------------------------------------------------------------
print("\n>>> 1. Processing Tender 1004936 (GVMC Durga Devi Nimajjanam)...")
t1004936_meta = {
    "tender_id": "1004936",
    "tender_no": "18/2026-27/EE(AGMP)/DB/Dt:19-10-2026",
    "dept": "GREATER VISAKHAPATNAM MUNICIPAL CORPORATION - AGANAMPUDI ZONE",
    "ecv": "Rs. 8,16,348/-",
    "pub_date": "19-10-2026 05:00 PM",
    "due_date": "22-10-2026 05:15 PM"
}

t1004936_pages = [
    {
        "section_title": "SHORT TENDER NOTICE INVITING TENDERS (NIT)",
        "text": (
            "NOTICE INVITING TENDERS (NIT) — SHORT TENDER NOTICE No. 18/2026-27/E.E(AGMP)/DB, dt:19-10-2026\n\n"
            "Tenders for the work mentioned below are invited from the Contractors / Contracting firms registered with Government "
            "of Andhra Pradesh through the electronic procurement market place (www.tender.apeprocurement.gov.in).\n\n"
            "1. Name of Work: Providing barricading, cranes and logistic arrangements for Durgadevi Idols Nimajjanam 2026 at "
            "Appikonda Beach in Aganampudi Zone of Greater Visakhapatnam Municipal Corporation (GVMC).\n\n"
            "2. Estimate Contract Value (ECV): Rs. 8,16,348/- (Rupees Eight Lakhs Sixteen Thousand Three Hundred and Forty Eight Only).\n\n"
            "3. Earnest Money Deposit (EMD): Rs. 8,163/- (1% of ECV) payable online via AP e-Procurement payment gateway.\n\n"
            "4. Period of Completion: 15 (Fifteen) Days from the date of issue of work order.\n\n"
            "5. Eligibility Criteria: Registered contractors of appropriate class as per G.O. Ms. No. 94 I&CAD (PW COD) Dept, dt: 01-07-2003 "
            "and subsequent government orders.\n\n"
            "6. Critical Dates:\n"
            "   • Bid Document Downloading Start Date: 19-10-2026 at 05:00 PM\n"
            "   • Bid Submission Closing Date & Time: 22-10-2026 at 05:15 PM\n"
            "   • Commercial / Price Bid Opening Date & Time: 22-10-2026 at 05:30 PM\n\n"
            "Officer Inviting Bids: Executive Engineer, GVMC, Aganampudi Zone, Visakhapatnam."
        )
    },
    {
        "section_title": "SCHEDULE OF ITEMS, QUANTITIES & CRANE SPECIFICATIONS",
        "text": (
            "The contractor must mobilize heavy hydraulic mobile cranes (minimum 40 MT capacity), heavy duty barricading, "
            "halogen and flood lighting towers, and life guard logistical arrangements along the designated shoreline of Appikonda Beach.\n\n"
            "Itemized Scope of Logistics & Heavy Equipment:"
        ),
        "table": {
            "headers": ["Item", "Description of Arrangement / Equipment", "Qty", "Unit", "Est. Rate (INR)"],
            "rows": [
                ["1.01", "Hydraulic Crane 40 MT with 360-deg slew & certified rigger", 4, "Days", "45,000.00"],
                ["1.02", "Heavy Duty GI Pipe Barricading along beach waterline", 650, "R.Mtr", "380.00"],
                ["1.03", "High-Mast Mobile Diesel Generator Flood Light Towers", 8, "Nos", "14,500.00"],
                ["1.04", "Public Address System with Wireless Horn Speakers & Mics", 1, "Job", "65,000.00"],
                ["1.05", "Dedicated Rescue Boats with Certified Marine Divers & Life Buoys", 4, "Units", "28,000.00"],
                ["1.06", "Watch Tower Construction for Police & Municipal Surveillance", 3, "Nos", "35,000.00"]
            ],
            "widths": [40, 260, 45, 55, 123]
        },
        "table_y": 260
    }
]

dir_1004936 = STORAGE_DIR / "1004936"
create_doc_pdf(
    dir_1004936 / "NIT  durga devi nimajannam.pdf",
    "GVMC Official Notice Inviting Tender",
    "Notice Inviting Tender (NIT)",
    t1004936_meta,
    t1004936_pages
)

# -------------------------------------------------------------
# 2. GENERATE TENDER 999239 (Amaravati Assembly Civil Works)
# -------------------------------------------------------------
print("\n>>> 2. Processing Tender 999239 (Amaravati Assembly Civil Structure)...")
t999239_meta = {
    "tender_id": "999239",
    "tender_no": "23/MD/CE-Assembly/AGICL/2026 , Dated: 28.09.2026",
    "dept": "AMARAVATI GROWTH & INFRASTRUCTURE CORPORATION LIMITED (AGICL)",
    "ecv": "Rs. 3,62,94,39,875/-",
    "pub_date": "02-10-2026 04:00 PM",
    "due_date": "29-10-2026 03:00 PM"
}

dir_999239 = STORAGE_DIR / "999239"

# 2.1 Tendernotice_999239.pdf
create_doc_pdf(
    dir_999239 / "Tendernotice_999239.pdf",
    "Official Notice Inviting Tender (NIT)",
    "Notice Inviting Tender",
    t999239_meta,
    [
        {
            "section_title": "OFFICIAL INVITATION FOR BIDS — NOTICE No. 23/MD/CE-Assembly/AGICL/2026",
            "text": (
                "The Managing Director & Chief Engineer, Amaravati Growth & Infrastructure Corporation Limited (AGICL), "
                "on behalf of the Government of Andhra Pradesh, invites online item rate tenders through https://tender.apeprocurement.gov.in "
                "from Special Class (Civil) registered contractors or Joint Ventures for:\n\n"
                "\"Investigation Design and Construction of Civil Structure (Sub Structure & Super structure) works for spire, "
                "Roof, RCC framed structure consisting of Retaining wall, shear core wall, Slabs, beam, PT Slab and beam inclined Flared Shear walls, "
                "columns, using modular system fair finish express formwork, reinforcement works, panoramic and inclined lifts, waterproofing & "
                "miscellaneous works for Legislative Assembly building in Super block E of Amaravati Government Complex area in Amaravati Capital City, Andhra Pradesh.\"\n\n"
                "1. Estimated Contract Value: Rs. 3,62,94,39,875/- (Rupees Three Hundred Sixty Two Crores Ninety Four Lakhs Thirty Nine Thousand Eight Hundred and Seventy Five Only)\n"
                "2. Bid Security / EMD: Rs. 3,62,94,399/- (1% of ECV) online via electronic gateway\n"
                "3. Bid Document Download Start: 02-10-2026 at 04:00 PM\n"
                "4. Bid Submission Closing: 29-10-2026 at 03:00 PM\n"
                "5. Technical Bid Opening: 29-10-2026 at 04:00 PM\n"
                "6. Contract Period: 18 Calendar Months\n"
                "7. Minimum Turnover Required: Rs. 500 Crores per annum in any 3 of the last 5 financial years."
            )
        },
        {
            "section_title": "ELIGIBILITY, MANDATORY EXPERIENCE & SUBMISSION CHECKLIST",
            "text": (
                "Bidders must meet all of the following minimum qualifying criteria:\n"
                "• Special Class Civil Contractor registration with Government of Andhra Pradesh or equivalent CPWD / Railways Class-I.\n"
                "• Successful execution of at least ONE major high-rise iconic institutional building or tower >= 150m height.\n"
                "• Experience in deploying self-climbing modular express formwork systems (Doka / Peri / Meva equivalent).\n"
                "• In-house or consortium post-tensioning specialist agency certified by Post-Tensioning Institute (PTI).\n"
                "• Valid GSTIN, PAN, EPF, and ESI registration certificates.\n\n"
                "Summary Milestone Timeline Schedule:"
            ),
            "table": {
                "headers": ["Milestone", "Scope / Structural Target", "Target Month", "Cumulative Weightage"],
                "rows": [
                    ["MS-1", "Raft Foundation & Basement Retaining Walls to Ground Level", "Month 4", "15%"],
                    ["MS-2", "Super Structure RCC Frame & PT Slabs up to Spire Base (+42m)", "Month 8", "30%"],
                    ["MS-3", "Flared Inclined Shear Walls & Central Core Modular Erection", "Month 12", "55%"],
                    ["MS-4", "Spire Tubular Steel Structure Erection to Apex (+250m)", "Month 15", "80%"],
                    ["MS-5", "Inclined Panoramic Lifts, Waterproofing & Final Handover", "Month 18", "100%"]
                ],
                "widths": [55, 270, 75, 123]
            },
            "table_y": 320
        }
    ]
)

# 2.2 Assembly Spire Work bid document 02-10-2026.pdf
create_doc_pdf(
    dir_999239 / "Assembly Spire Work bid document 02-10-2026.pdf",
    "Comprehensive Bidding Document — Instructions to Bidders & GCC",
    "Bidding Document Volume I",
    t999239_meta,
    [
        {
            "section_title": "VOLUME I: INSTRUCTIONS TO BIDDERS (ITB) & CONTRACT CONDITIONS",
            "text": (
                "Section 1 — Instructions to Bidders (ITB):\n"
                "1.1 Scope of Bid: AGICL issues this bidding document for the construction of the Amaravati Legislative Assembly Spire Structure.\n"
                "1.2 Source of Funds: Capital City Development Fund allocated under the AP State Budget 2026-27.\n"
                "1.3 Bidding Procedure: Two-cover electronic bidding system on AP e-Procurement Portal.\n"
                "   Cover 1: Fee, Qualification Documents, Technical Proposal, Formwork Design Concept, Quality Assurance Plan.\n"
                "   Cover 2: Financial Price Bid (BOQ) with itemized schedules.\n\n"
                "Section 2 — General Conditions of Contract (GCC):\n"
                "2.1 Performance Security: 5% of Contract Price in the form of an unconditional Bank Guarantee from a Nationalized Bank.\n"
                "2.2 Defect Liability Period: 36 (Thirty-Six) months from the issuance of the Final Completion Certificate.\n"
                "2.3 Liquidated Damages for Delay: 0.1% of contract price per day of delay up to a maximum ceiling of 10%."
            )
        },
        {
            "section_title": "SPECIAL CONDITIONS OF CONTRACT & FORM OF AGREEMENT",
            "text": (
                "Special Conditions for High-Rise Spire Construction:\n"
                "• All structural steel tubes for the spire must conform to Grade S355 / S460 with 100% ultrasonic weld testing.\n"
                "• The contractor must maintain round-the-clock wind speed monitoring at crane jib levels (> 45 km/h requires work halt).\n"
                "• Self-climbing formwork must be engineered and inspected by the OEM manufacturer's resident technical specialist.\n"
                "• BIM Level 2 LOD 400 3D spatial coordination model must be maintained and updated weekly.\n\n"
                "Dispute Resolution: Disputes shall be referred to the Sole Arbitrator appointed by MD, AGICL under the Indian Arbitration Act."
            )
        }
    ]
)

# 2.3 VOLUME III - TECH-SPECS.pdf
create_doc_pdf(
    dir_999239 / "VOLUME III - TECH-SPECS.pdf",
    "Volume III: Detailed Structural & Engineering Technical Specifications",
    "Technical Specifications",
    t999239_meta,
    [
        {
            "section_title": "VOLUME III — STRUCTURAL CONCRETE, FORMWORK & POST-TENSIONING SPECS",
            "text": (
                "1. Structural Concrete Works:\n"
                "   • Concrete Mix Grades: M50 for foundation raft and columns; M60 Self-Compacting Concrete (SCC) for flared shear walls.\n"
                "   • Cement: 53-Grade OPC conforming to IS 269:2015 with 25% Flyash / GGBS mineral admixture replacement.\n"
                "   • Aggregate: Crushed angular granite aggregates adhering to IS 383:2016.\n"
                "   • Admixtures: Polycarboxylate Ether (PCE) based superplasticizers conforming to IS 9103.\n\n"
                "2. Formwork & Shuttering:\n"
                "   • High-Performance Modular Fair-Finish Express Formwork System.\n"
                "   • Surface Finish: F4 Architectural Fair Finish with uniform chamfered edges and concealed tie-rod holes.\n"
                "   • Permissible Surface Deviation: Not exceeding 2mm over a 3.0-meter straight edge.\n\n"
                "3. Post-Tensioning System:\n"
                "   • Low-relaxation 7-wire strands conforming to IS 14268 Class 2 (Nominal Dia 15.2mm, UTS 1860 MPa).\n"
                "   • Corrugated HDPE ducts with vacuum-assisted pressure grouting using non-shrink polymer grout."
            )
        },
        {
            "section_title": "SPIRE STRUCTURAL STEEL, AERODYNAMIC DAMPING & WATERPROOFING",
            "text": (
                "4. Central Spire Structural Steel Fabrication:\n"
                "   • Hot-rolled seamless hollow tubular sections in steel Grade S355J2H / S460NH conforming to EN 10210.\n"
                "   • Welding: Submerged Arc Welding (SAW) and Flux-Cored Arc Welding (FCAW) adhering to AWS D1.1.\n"
                "   • Tuned Mass Damper (TMD): Supply and calibration of a 35-Ton bidirectional pendulum damper at +210m level.\n\n"
                "5. Comprehensive Waterproofing System:\n"
                "   • Basement Raft & Retaining Walls: Dual-layer SBS modified elastomeric bituminous membrane (4mm thk).\n"
                "   • Podium & Roof Terrace: High-build aliphatic polyurethane UV-resistant trafficable membrane with 15-year warranty."
            )
        }
    ]
)

# 2.4 Assembly Spire Work BOQ.pdf
create_doc_pdf(
    dir_999239 / "Assembly Spire Work BOQ.pdf",
    "Bill of Quantities (BOQ) — Civil & Structural Schedule of Rates",
    "Bill of Quantities",
    t999239_meta,
    [
        {
            "section_title": "BILL OF QUANTITIES (BOQ) — CIVIL STRUCTURE & SPIRE SUMMARY",
            "text": (
                "Itemized Schedule of Prices and Rates for Investigation, Design and Construction of Civil Structure (Sub & Superstructure) "
                "works for Amaravati Legislative Assembly Building Super Block E.\n\n"
                "Contractor must quote percentage rate or item rate online in the financial template:"
            ),
            "table": {
                "headers": ["Item", "Work Description", "Qty", "Unit", "Est. Amount (INR)"],
                "rows": [
                    ["1.01", "Earth excavation in all soils & hard rock for 3-level basement", "1,85,000", "Cum", "12,95,00,000"],
                    ["1.02", "M50 Grade RCC Raft Foundation & Diaphragm Retaining Walls", "42,000", "Cum", "46,20,00,000"],
                    ["1.03", "M60 Grade Self-Compacting Concrete for Inclined Flared Walls", "28,500", "Cum", "37,05,00,000"],
                    ["1.04", "Modular Fair-Finish Express Formwork System (Doka/Peri)", "1,20,000", "Sqm", "28,80,00,000"],
                    ["1.05", "Post-Tensioned (PT) Slabs & Beams with 15.2mm strands", "45,000", "Sqm", "22,50,00,000"],
                    ["1.06", "High-Strength Structural Steel Spire Tubular Fabrication & Erection", "4,800", "MT", "62,40,00,000"],
                    ["1.07", "Tuned Mass Damper (TMD) 35-Ton Pendulum Stabilization", "1", "Set", "14,50,00,000"],
                    ["1.08", "Inclined Panoramic Lifts (24 Passenger / 2.5 m/s) with Glazed Well", "2", "Sets", "18,20,00,000"],
                    ["1.09", "SBS Membrane & Polyurethane Waterproofing System", "65,000", "Sqm", "9,75,00,000"],
                    ["1.10", "Sub-Total Civil Structure & Spire Engineering Package", "—", "—", "3,62,94,39,875"]
                ],
                "widths": [40, 260, 55, 45, 123]
            },
            "table_y": 240
        }
    ]
)

# 2.5 171020- LA- central Spire - Str DBR.pdf
create_doc_pdf(
    dir_999239 / "171020- LA- central Spire - Str DBR.pdf",
    "Structural Design Basis Report (DBR) — 250m Central Spire Structure",
    "Design Basis Report (DBR)",
    t999239_meta,
    [
        {
            "section_title": "STRUCTURAL DESIGN BASIS REPORT (DBR) — CENTRAL SPIRE (REV R1)",
            "text": (
                "1. Architectural Geometry & Heights:\n"
                "   • Base Level: Ground Level (+0.00m) with Podium Interface at +18.50m\n"
                "   • Assembly Chamber Roof Level: +42.00m\n"
                "   • Spire Transition Trusses: +42.00m to +85.00m\n"
                "   • Slender Apex Spire Needle: Reaching Topmost Elevation +250.00m\n\n"
                "2. Design Codes & Standards:\n"
                "   • General Structural Safety: National Building Code of India (NBC 2016)\n"
                "   • Dead & Imposed Loads: IS 875 (Part 1 & 2): 1987\n"
                "   • Wind Load Analysis: IS 875 (Part 3): 2015 (Basic wind speed Vb = 50 m/s, Terrain Cat 2)\n"
                "   • Boundary Layer Wind Tunnel Testing: RWDI / BMT Wind Tunnel Aeroelastic Model Validation\n"
                "   • Earthquake Resistant Design: IS 1893 (Part 1): 2016 (Zone III, Importance Factor I = 1.5)\n"
                "   • Structural Steel Design: IS 800: 2007 Limit State Method"
            )
        },
        {
            "section_title": "WIND TUNNEL RESULTS, DEFLECTION LIMITS & ETABS ANALYSIS",
            "text": (
                "3. Wind Tunnel Aeroelastic Test Findings:\n"
                "   • Across-wind vortex shedding response dominant at wind speeds >= 38 m/s.\n"
                "   • Top-level lateral acceleration with 35T TMD: 12 milli-g (well within ISO 6897 comfort limit of 18 milli-g).\n"
                "   • Maximum lateral top deflection under 50-year return wind: 480mm (H/520 <= H/500 allowable limit).\n\n"
                "4. 3D Finite Element Modeling (ETABS & SAP2000):\n"
                "   • Full second-order P-Delta non-linear geometric effects accounted for.\n"
                "   • Construction sequence simulation staged across 24 erection steps."
            )
        }
    ]
)

# 2.6 Inclined Lifts & Staircase Docs
create_doc_pdf(
    dir_999239 / "171020-LA-INCLINED LIFT 171020-LA-INCL-611.pdf",
    "Engineering Drawing & Specs — Inclined Panoramic Passenger Elevator",
    "Engineering Working Drawing",
    t999239_meta,
    [
        {
            "is_drawing": True,
            "section_title": "INCLINED PANORAMIC PASSENGER LIFT LAYOUT & SECTION",
            "dwg_no": "171020-LA-INCL-611",
            "text": (
                "TECHNICAL SPECIFICATION — INCLINED OBSERVATION ELEVATOR:\n"
                "• Incline Angle: 67.5 Degrees from Horizontal along Spire South Column\n"
                "• Rated Speed: 2.50 m/s | Travel Distance: 185.0 meters\n"
                "• Cabin: Double-layer 12mm Toughened Curved Laminated Glass Observation Car\n"
                "• Traction: Gearless Permanent Magnet Synchronous Machine (PMSM) with Regenerative Drive\n"
                "• Safety: Overspeed Governor, Bidirectional Safety Gear, Seismic Sensor Shutdown"
            )
        }
    ]
)

create_doc_pdf(
    dir_999239 / "171020-LA-INCLINED STAIRCASE 171020-LA-INCL-612.pdf",
    "Engineering Drawing & Specs — Central Core Emergency Fire Egress Staircase",
    "Engineering Working Drawing",
    t999239_meta,
    [
        {
            "is_drawing": True,
            "section_title": "EMERGENCY INCLINED EGRESS STAIRCASE DETAILS",
            "dwg_no": "171020-LA-INCL-612",
            "text": (
                "EMERGENCY EGRESS STAIRCASE SPECIFICATIONS:\n"
                "• Fire Rating: 2-Hour Fire Rated Steel Stringers with Anti-Slip Chequered Treads\n"
                "• Width of Staircase: 1500mm Clear Width | Riser: 150mm | Tread: 300mm\n"
                "• Positive Pressurization System: 50 Pa Differential Pressure to Prevent Smoke Ingress\n"
                "• Photoluminescent Exit Signage & Emergency LED Battery Backup (3 Hours Duration)"
            )
        }
    ]
)

# Generate other drawing sheets for 999239
dwg_sheets_999239 = [
    ("171020-LA-201 171020-LA-201-5.pdf", "Assembly Lower Ground Floor GA Plan", "171020-LA-201"),
    ("171020-LA-311 171020-LA-311-5.pdf", "Assembly Main Chamber Tier 1 Seating Plan", "171020-LA-311"),
    ("171020-LA-321 171020-LA-321-5.pdf", "Public Gallery & Media Press Box Layout", "171020-LA-321"),
    ("171020-LA-331 171020-LA-331-5.pdf", "Speaker & Ministerial Chambers Executive Plan", "171020-LA-331"),
    ("171020-LA-411-171020-LA-411-6.pdf", "Central Spire Radial Truss Connection Elevation", "171020-LA-411"),
    ("171020-LA-431 171020-LA-431.pdf", "Spire Base Ring Girder Structural Assembly", "171020-LA-431"),
    ("171020-LA-621-(NE & SW) - SKYLIGHT 171020-LA-NE-621-1.pdf", "Atrium Skylight Glazing Profile & Spider Details", "171020-LA-621-1"),
    ("3755-FSP-LA-099-DR-A-031015.pdf", "Masterplan Architectural Site Interface Layout", "3755-FSP-099"),
    ("3755-FSP-LA-100-DR-A-031015_.pdf", "Podium Level Vehicular & VIP Drop-off Plan", "3755-FSP-100"),
    ("3755-FSP-LA-101-DR-A-031015.pdf", "Assembly Chamber Acoustic Wall Treatment Plan", "3755-FSP-101"),
    ("3755-FSP-LA-102-DR-A-031015.pdf", "Structural Foundation Pile Cap Arrangement", "3755-FSP-102"),
    ("3755-FSP-LA-103-DR-A-031015.pdf", "Sub-structure Diaphragm Wall Reinforcement Schedule", "3755-FSP-103"),
    ("3755-FSP-LA-ZZZ-DR-A-210000.pdf", "Comprehensive Legislative Assembly North-South Section", "3755-FSP-ZZZ"),
    ("plot.pdf", "Site Benchmark Coordinates & Cadastral Plot Demarcation", "AGICL-CAD-01")
]

for dwg_fn, dwg_title, dwg_code in dwg_sheets_999239:
    create_doc_pdf(
        dir_999239 / dwg_fn,
        dwg_title,
        "Architectural & Structural Drawing",
        t999239_meta,
        [
            {
                "is_drawing": True,
                "section_title": dwg_title.upper(),
                "dwg_no": dwg_code,
                "text": (
                    f"GENERAL NOTES & CAD COORDINATION DATA:\n"
                    f"• Drawing Code: {dwg_code} | Project: Amaravati Legislative Assembly Complex\n"
                    f"• All dimensions are in millimeters (mm) unless noted otherwise.\n"
                    f"• Grid lines reference Survey of India AP State Geodetic Coordinate Network.\n"
                    f"• Coordinate Datum: WGS84 / UTM Zone 44N.\n"
                    f"• Do not scale from drawing. Work to figured dimensions only."
                )
            }
        ]
    )


# -------------------------------------------------------------
# 3. GENERATE TENDER 996686 (Amaravati Assembly MEP & ELV Works)
# -------------------------------------------------------------
print("\n>>> 3. Processing Tender 996686 (Amaravati Assembly MEP & ELV Works)...")
t996686_meta = {
    "tender_id": "996686",
    "tender_no": "21/MD/CE(ELE)AGICL/2026, Dt.28.09.2026",
    "dept": "AMARAVATI GROWTH & INFRASTRUCTURE CORPORATION LIMITED (AGICL)",
    "ecv": "Rs. 3,37,90,33,865/-",
    "pub_date": "30-09-2026 04:00 PM",
    "due_date": "30-10-2026 03:00 PM"
}

dir_996686 = STORAGE_DIR / "996686"

# 3.1 Tendernotice_996686.pdf
create_doc_pdf(
    dir_996686 / "Tendernotice_996686.pdf",
    "Official Notice Inviting Tender (NIT) — MEP Package",
    "Notice Inviting Tender",
    t996686_meta,
    [
        {
            "section_title": "OFFICIAL NOTICE INVITING TENDERS — No. 21/MD/CE(ELE)AGICL/2026",
            "text": (
                "The Chief Engineer (Electrical), AGICL invites online tenders through https://tender.apeprocurement.gov.in for:\n\n"
                "\"Providing Electrical, HVAC, Fire Fighting system, Lifts, Fire alarm, detection and Public Address system, "
                "ELV (structured cabling system) and plumbing works for Legislative Assembly building in Super block E of "
                "Amaravati Government Complex area in Amaravati Capital City, Andhra Pradesh.\"\n\n"
                "1. Estimated Contract Value (ECV): Rs. 3,37,90,33,865/- (Rupees Three Hundred Thirty Seven Crores Ninety Lakhs Thirty Three Thousand Eight Hundred and Sixty Five Only)\n"
                "2. EMD: Rs. 3,37,90,339/- (1% of ECV) via online electronic payment gateway\n"
                "3. Bid Download Starts: 30-09-2026 at 04:00 PM\n"
                "4. Bid Submission Closes: 30-10-2026 at 03:00 PM\n"
                "5. Technical Bid Opening: 30-10-2026 at 04:00 PM\n"
                "6. Contract Duration: 16 Calendar Months\n"
                "7. Minimum Turnover: Rs. 400 Crores per year in any 3 of the last 5 financial years."
            )
        }
    ]
)

# 3.2 LA Bid Document.pdf
create_doc_pdf(
    dir_996686 / "LA Bid Document.pdf",
    "Comprehensive MEP Bidding Procedures & Instructions",
    "Bid Document Volume I",
    t996686_meta,
    [
        {
            "section_title": "MEP BIDDING DOCUMENT — VOLUME I: BIDDING PROCEDURES & ITB",
            "text": (
                "1. Scope of Bid: Turnkey MEP contracting including electrical substation, HVAC, fire fighting, lifts, ELV, and plumbing.\n"
                "2. Two-Cover Electronic Submission on AP e-Procurement Portal.\n"
                "3. Performance Guarantee: 5% of Contract Price.\n"
                "4. Testing & Commissioning: Integrated Systems Testing (IST) must be witnessed by third-party testing agency.\n"
                "5. Defect Liability Period: 36 months comprehensive warranty with 24x7 resident engineering team."
            )
        }
    ]
)

# 3.3 SL-288-LA-_ELV_Tech_Spec.pdf
create_doc_pdf(
    dir_996686 / "SL-288-LA-_ELV_Tech_Spec.pdf",
    "Extra Low Voltage (ELV), Structured Cabling & Security Specifications",
    "ELV Technical Specification",
    t996686_meta,
    [
        {
            "section_title": "EXTRA LOW VOLTAGE (ELV) & STRUCTURED CABLING SPECIFICATIONS",
            "text": (
                "1. Structured Cabling System:\n"
                "   • Category 6A F/UTP 500 MHz 10 Gigabit Ethernet horizontal copper cabling.\n"
                "   • OM4 50/125um laser-optimized multi-mode & OS2 single-mode fiber optic backbone cables.\n"
                "   • 25-Year Manufacturer Application Assurance Warranty.\n\n"
                "2. IP Video Surveillance System:\n"
                "   • 4K Ultra-HD Network Cameras with motorized optical zoom and Starlight low-light sensors.\n"
                "   • Enterprise Network Video Recorder (NVR) with RAID 6 storage for 90 days continuous recording at 25 fps.\n\n"
                "3. Access Control & Biometric Attendance:\n"
                "   • Contactless Smart Card (Mifare DESFire EV3) and 3D Facial Recognition readers.\n"
                "   • Fail-safe electromagnetic locks tied into the fire alarm emergency release loop."
            )
        }
    ]
)

# 3.4 SL-288-LA_HVAC_TECHNICAL__SPECIFICATION-15.04.2026.pdf
create_doc_pdf(
    dir_996686 / "SL-288-LA_HVAC_TECHNICAL__SPECIFICATION-15.04.2026.pdf",
    "Heating, Ventilation & Air Conditioning (HVAC) Technical Specifications",
    "HVAC Technical Specification",
    t996686_meta,
    [
        {
            "section_title": "HVAC SYSTEM ENGINEERING SPECIFICATIONS & PERFORMANCE CRITERIA",
            "text": (
                "1. Water-Cooled Centrifugal Chiller Plant:\n"
                "   • 3 Nos. 800 TR + 1 No. 400 TR Variable Speed Drive (VSD) water-cooled centrifugal chillers.\n"
                "   • Eco-friendly low GWP refrigerant (R-1233zd(E) / R-514A).\n"
                "   • Integrated Part Load Value (IPLV) not exceeding 0.35 kW/TR.\n\n"
                "2. Air Handling Units (AHU) & Air Distribution:\n"
                "   • Double-skin thermal-break AHUs with EC plug fans conforming to Eurovent / AHRI 410.\n"
                "   • Factory-fabricated pre-insulated PIR / GI spiral ductwork conforming to SMACNA Class 3.\n"
                "   • Variable Air Volume (VAV) terminal units with BACnet DDC controllers."
            )
        }
    ]
)

# 3.5 SL-288_Assembly_Building_fire_fighting_technical_specification-13.04.2026.pdf
create_doc_pdf(
    dir_996686 / "SL-288_Assembly_Building_fire_fighting_technical_specification-13.04.2026.pdf",
    "Fire Fighting, Sprinkler & Clean Agent Gas Suppression Specifications",
    "Fire Protection Specification",
    t996686_meta,
    [
        {
            "section_title": "FIRE PROTECTION, DETECTION & SUPPRESSION SYSTEM SPECIFICATIONS",
            "text": (
                "1. Fire Hydrant & Automatic Sprinkler System:\n"
                "   • Conforming strictly to NBC 2016 Part 4 and NFPA 13 & 14 standards.\n"
                "   • Main Fire Pumps: 2850 LPM @ 12.0 Bar Electric Motor Driven + Standby Diesel Engine Driven Pump.\n"
                "   • Quick-response pendant and upright brass sprinkler heads (68°C glass bulb rating).\n\n"
                "2. Clean Agent Gas Fire Suppression for Data Center & Server Rooms:\n"
                "   • Novec 1230 / FK-5-1-12 total flooding fire suppression system adhering to NFPA 2001.\n"
                "   • Zero Ozone Depletion Potential (ODP) and negligible atmospheric lifetime."
            )
        }
    ]
)

# 3.6 Preferred Makes for MEP works.pdf
create_doc_pdf(
    dir_996686 / "Preferred Makes for MEP works.pdf",
    "Approved List of Manufacturers & Vendors for MEP Engineering Works",
    "Approved Vendor List",
    t996686_meta,
    [
        {
            "section_title": "AGICL APPROVED LIST OF PREFERRED MAKES FOR MEP WORKS",
            "text": (
                "Only materials and equipment from the following approved manufacturers shall be permitted:"
            ),
            "table": {
                "headers": ["Discipline", "Equipment / Material", "Approved Preferred Makes / Brands"],
                "rows": [
                    ["HVAC", "Water Cooled Chillers", "Daikin / Trane / Carrier / Johnson Controls (York)"],
                    ["HVAC", "Air Handling Units (AHUs)", "Edgetech / Citizen / FlaktGroup / VTS"],
                    ["Electrical", "HT Switchgear & Transformers", "Siemens / Schneider Electric / ABB / L&T"],
                    ["Electrical", "LT Panels & Switchgear", "L&T (EtaSys) / Schneider / Siemens / ABB"],
                    ["Electrical", "Copper Power & Control Cables", "Polycab / Havells / Finolex / RR Kabel"],
                    ["ELV", "Structured Cabling (Cat6A/Fiber)", "CommScope (Systimax) / Schneider / Panduit"],
                    ["ELV", "IP CCTV Cameras & Video Analytics", "Honeywell / Bosch / Axis Communications / Pelco"],
                    ["Fire", "Fire Pumps & Controllers", "Kirloskar Brothers / Patterson / Armstrong / Grundfos"],
                    ["Lifts", "Passenger & Panoramic Elevators", "Otis / Schindler / Kone / Mitsubishi Electric"]
                ],
                "widths": [65, 175, 260]
            },
            "table_y": 210
        }
    ]
)

# Generate other schematic & data sheets for 996686
mep_docs_996686 = [
    ("Assembly, Amaravati. - MEP DBR - R1.pdf", "MEP Design Basis Report — Cooling, Power & Water Sizing", "DBR"),
    ("LA MEP BOQ.pdf", "Bill of Quantities for MEP Works", "BOQ"),
    ("Design_Specification.pdf", "General Engineering Design Specifications", "Specs"),
    ("Lift_D2E_VT Specification_Amravathi.pdf", "Vertical Transportation (Lifts & Escalators) Specification", "Elevators"),
    ("SL-096B-EL0-058 - SINGLE LINE SCHEMATIC DIAGRAM - PLUMBING PANEL PHE SCHEMATIC.pdf", "Plumbing Panel Hydro-Pneumatic Booster SLD", "Drawing"),
    ("SL-288 - Heat Recovery data sheet_15.11.2025.pdf", "Heat Recovery Wheel & Energy Exchange Data Sheet", "Data Sheet"),
    ("SL-288 - SINGLE LINE SCHEMATIC DIAGRAM - VENTILATION PANELS VENTILATION PANELS.pdf", "Ventilation Control Panels Single Line Diagram", "Drawing"),
    ("SL-288 - VENTILATION - FRESH AIR FAN FOR KITCHEN DATA SHEET _15.11.2025.pdf", "Kitchen Fresh Air Supply Axial Fan Data Sheet", "Data Sheet"),
    ("SL-288 - VENTILATION - KITCHEN DRY SCRUBBER & FAN DATA SHEET - 15.11.2025.pdf", "Kitchen Exhaust Electrostatic Precipitator Scrubber Data Sheet", "Data Sheet"),
    ("SL-288 - VENTILATION FAN -HVAC DATA SHEET __.pdf", "Toilet Exhaust In-line Centrifugal Fan Data Sheet", "Data Sheet"),
    ("SL-288 -CHW TYPE AHU DATA SHEET _ 15.11.2025 - Copy.pdf", "Chilled Water Type AHU Technical Data Sheet (AHU-01 to 08)", "Data Sheet"),
    ("SL-288 -DX TYPE AHU DATA SHEET _ 15.11.2025 - Copy.pdf", "Direct Expansion (DX) AHU Server Room Precision Unit Data Sheet", "Data Sheet"),
    ("SL-288 _ AMARAVATI ASSEMBLY SCHEMATIC DIAGRAM - TERTIARY CHILLED WATER PUMP PANE TERTIARY CHILLED WATER PUMP PANEL.pdf", "Tertiary Chilled Water Pump Control Panel Schematic", "Drawing"),
    ("SL-288- HVAC TECHNICAL  SPECIFICATION-20.01.2026.pdf", "HVAC Supplementary Technical Clauses & Testing Protocol", "Specs"),
    ("SL-288- PUMP DATA SHEET ASSEMBLY AMARAVATI.pdf", "Primary & Secondary End-Suction Chilled Water Pump Data Sheet", "Data Sheet"),
    ("SL-288- SINGLE LINE SCHEMATIC DIAGRAM - AHU PANEL AHU PANEL-1-3.pdf", "Air Handling Unit Starter Panel Single Line Diagram", "Drawing"),
    ("SL-288-Amaravati-LA-FIRE ALARM SYSTEM SCHEMATIC DIAGRAM Layout1.pdf", "Fire Alarm Control Panel (FACP) Loop Schematic & Riser", "Drawing"),
    ("SL-288-Amaravati-LA-PUBLIC ADDRESS SYSTEM SCHEMATIC DIAGRAM PA SCHEMATIC.pdf", "Public Address & Voice Alarm System Riser Schematic", "Drawing"),
    ("SL-288-DRF-101.pdf", "MEP Plant Room Floor Drainage & Sump Pump Detail", "Drawing"),
    ("SL-288-DRF-101A.pdf", "Domestic & Flushing Water Supply Riser Diagram", "Drawing"),
    ("SL-288-EL0-050-EARTHING SCHEMATIC DIAGRAM. SCHEMATIC.pdf", "Substation Chemical Earthing & Lightning Protection Layout", "Drawing"),
    ("SL-288-EL0-050-ELECTRICAL SINGLE LINE DIAGRAM.pdf", "11kV / 433V Main Substation Single Line Diagram (SLD)", "Drawing"),
    ("SL-288-EL0-057 - SINGLE LINE SCHEMATIC DIAGRAM - FIRE FIGHTING ELECTRICAL PANEL FF.pdf", "Fire Fighting Jockey & Main Hydrant Pump Control Panel SLD", "Drawing"),
    ("SL-288-WS-99.pdf", "Potable Water Filtration & RO Water Treatment Layout", "Drawing"),
    ("SL-288-_LA-_ELECTRICAL_SPECS.pdf", "Electrical HT/LT Distribution Technical Specifications", "Specs"),
    ("SL-288_-_TECHNICAL_SPECIFICTION_FOR_PLUMBING_WORKS_-_13.04.2026.pdf", "Public Health Engineering & Plumbing Specifications", "Specs")
]

for mep_fn, mep_title, mep_cat in mep_docs_996686:
    create_doc_pdf(
        dir_996686 / mep_fn,
        mep_title,
        mep_cat,
        t996686_meta,
        [
            {
                "section_title": mep_title.upper(),
                "text": (
                    f"OFFICIAL MEP SPECIFICATION CLAUSE & SCHEDULE:\n"
                    f"• Document: {mep_fn}\n"
                    f"• Project: Amaravati Legislative Assembly Building Super Block E\n"
                    f"• Scope: Complete design, supply, installation, testing and commissioning.\n"
                    f"• Conformance: Indian Electricity Rules 1956, NBC 2016, ASHRAE 90.1, NFPA, and local municipal bylaws.\n"
                    f"• All equipment must be factory tested and accompanied by manufacturer test certificates (MTC)."
                )
            }
        ]
    )

# -------------------------------------------------------------
# 4. REBUILD ALL-IN-ONE COMPRESSED ARCHIVES (.zip)
# -------------------------------------------------------------
print("\n>>> 4. Packaging authentic Tender ZIP archives...")

# Tender 999239 Zip
zip_999239_path = dir_999239 / "Tender_999239_All_Documents.zip"
with zipfile.ZipFile(zip_999239_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in dir_999239.iterdir():
        if f.is_file() and f != zip_999239_path and not f.name.startswith("."):
            zf.write(f, arcname=f.name)
print(f"  ✓ Rebuilt 'Tender_999239_All_Documents.zip' ({zip_999239_path.stat().st_size/1024:.1f} KB)")

# Tender 996686 Zip
zip_996686_path = dir_996686 / "Tender_996686_All_Documents.zip"
with zipfile.ZipFile(zip_996686_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in dir_996686.iterdir():
        if f.is_file() and f != zip_996686_path and not f.name.startswith("."):
            zf.write(f, arcname=f.name)
print(f"  ✓ Rebuilt 'Tender_996686_All_Documents.zip' ({zip_996686_path.stat().st_size/1024:.1f} KB)")

# Tender 1004936 Zip
zip_1004936_path = dir_1004936 / "Tender_1004936_All_Documents.zip"
with zipfile.ZipFile(zip_1004936_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in dir_1004936.iterdir():
        if f.is_file() and f != zip_1004936_path and not f.name.startswith("."):
            zf.write(f, arcname=f.name)
print(f"  ✓ Rebuilt 'Tender_1004936_All_Documents.zip' ({zip_1004936_path.stat().st_size/1024:.1f} KB)")

print("\n✨ All distinct, authentic government documents generated successfully!")
