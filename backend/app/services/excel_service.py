import os
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.db.database import SessionLocal
from app.routers.reports import get_state_keyword_report

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_REPORTS_DIR = BASE_DIR / "storage" / "reports"
STORAGE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def format_dmy(val: Any) -> str:
    """Format a date or date string to Date, Month, Year format: e.g. '19 Oct 2026'."""
    if not val:
        return "-"
    if isinstance(val, str):
        try:
            val = datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            try:
                val = datetime.strptime(val[:10], "%Y-%m-%d")
            except Exception:
                return val
    if hasattr(val, "strftime"):
        return val.strftime("%d %b %Y")
    return str(val)


def generate_proposals_excel(
    report_data: Optional[List[Dict[str, Any]]] = None,
    output_filename: Optional[str] = None,
    base_api_url: str = "http://127.0.0.1:8000",
    base_app_url: str = "http://localhost:5173"
) -> Path:
    """
    Generate an executive-grade Excel workbook (.xlsx) containing all proposals,
    states, keywords, and authentic attached documents with direct one-click
    hyperlinks to download documents and open the web portal.
    """
    if report_data is None:
        db = SessionLocal()
        try:
            report_data = get_state_keyword_report(db)
        finally:
            db.close()

    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # STYLES DEFINITION
    # -------------------------------------------------------------
    navy_header_fill = PatternFill(start_color="1E1B4B", end_color="1E1B4B", fill_type="solid")
    indigo_sub_fill = PatternFill(start_color="312E81", end_color="312E81", fill_type="solid")
    light_zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    live_badge_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    closing_badge_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    upcoming_badge_fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Segoe UI", size=14, bold=True, color="1E1B4B")
    subtitle_font = Font(name="Segoe UI", size=10, italic=True, color="64748B")
    body_font = Font(name="Segoe UI", size=10, color="0F172A")
    bold_body_font = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
    link_font = Font(name="Segoe UI", size=10, color="2563EB", underline="single")
    badge_green_font = Font(name="Segoe UI", size=10, bold=True, color="166534")
    badge_red_font = Font(name="Segoe UI", size=10, bold=True, color="991B1B")
    badge_blue_font = Font(name="Segoe UI", size=10, bold=True, color="1E40AF")

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    grid_border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side
    )

    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right_align = Alignment(horizontal="right", vertical="center")

    # -------------------------------------------------------------
    # SHEET 1: PROPOSALS & ATTACHED DOCUMENTS
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Proposals & Documents"
    ws1.views.sheetView[0].showGridLines = True

    # Title Banner Rows
    ws1.merge_cells("A1:M1")
    title_cell = ws1["A1"]
    title_cell.value = "GISFY Automated Proposals — Master State & Keyword Intelligence"
    title_cell.font = title_font
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[1].height = 28

    ws1.merge_cells("A2:M2")
    sub_cell = ws1["A2"]
    sub_cell.value = f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')} • Interactive links included for instant document download & portal navigation"
    sub_cell.font = subtitle_font
    sub_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[2].height = 20

    # Column Headers
    headers = [
        "State",
        "Keyword",
        "Tender ID / Ref",
        "Tender Title",
        "Department / Agency",
        "Published Date",
        "Submission Due Date",
        "Status",
        "Document File Name",
        "Document Type",
        "Size (KB)",
        "Direct Document Download (Click Link)",
        "Open in GISFY Portal"
    ]

    header_row = 4
    ws1.row_dimensions[header_row].height = 28

    for col_idx, h in enumerate(headers, start=1):
        cell = ws1.cell(row=header_row, column=col_idx, value=h)
        cell.fill = navy_header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = grid_border

    current_row = 5
    row_count = 0

    for state in report_data:
        sname = state.get("state_name", "Unknown State")
        portal_url = state.get("portal_url") or "https://eprocure.gov.in"
        
        for kw_item in state.get("keywords", []):
            kw_name = kw_item.get("keyword", "")
            tenders = kw_item.get("tenders", [])

            for t in tenders:
                tid = t.get("tender_id") or f"TND-{t.get('id', '')}"
                title = t.get("title", "Untitled Proposal")
                dept = t.get("department", "State Agency")
                pub_date = t.get("published_date")
                pub_date_str = format_dmy(pub_date)
                due_date = t.get("last_date")
                due_date_str = format_dmy(due_date)

                stage = t.get("stage") or ("live" if t.get("is_live") else "upcoming")
                status_label = "🟢 LIVE ACTIVE" if stage == "live" else ("⚠️ CLOSING SOON" if stage == "closing_soon" else "⏳ UPCOMING")

                app_deep_link = f"{base_app_url}/?state={urllib.parse.quote(sname)}&keyword={urllib.parse.quote(kw_name)}&tender={urllib.parse.quote(str(tid))}"
                
                docs = t.get("documents", [])
                if not docs:
                    docs = [{
                        "id": None,
                        "file_name": "Portal Notice (Online Submission)",
                        "file_type": "Notice",
                        "file_size_kb": 0,
                        "local_path": None,
                        "sub_documents": []
                    }]

                for d in docs:
                    fname = d.get("file_name", "Document")
                    ext = d.get("file_type") or Path(fname).suffix or ".pdf"
                    fsize = d.get("file_size_kb", 0)

                    doc_type = "📕 PDF Document" if ext.lower() == ".pdf" else (
                        "📦 ZIP Package" if ext.lower() == ".zip" or d.get("is_bundle") else (
                            "📊 Excel BOQ" if ext.lower() in (".xls", ".xlsx") else f"📄 {ext.upper().replace('.', '')}"
                        )
                    )

                    doc_id = d.get("id")
                    local_path = d.get("local_path")
                    if doc_id and doc_id < 800000:
                        dl_url = f"{base_api_url}/api/documents/download?id={doc_id}&attachment=true"
                    elif local_path:
                        dl_url = f"{base_api_url}/api/documents/download?path={urllib.parse.quote(local_path)}&attachment=true"
                    else:
                        dl_url = t.get("portal_tender_url") or portal_url

                    fill = light_zebra_fill if row_count % 2 == 1 else white_fill
                    ws1.row_dimensions[current_row].height = 24

                    # Col 1: State
                    c1 = ws1.cell(row=current_row, column=1, value=sname)
                    c1.font = bold_body_font
                    c1.alignment = left_align
                    c1.fill = fill
                    c1.border = grid_border

                    # Col 2: Keyword
                    c2 = ws1.cell(row=current_row, column=2, value=kw_name)
                    c2.font = bold_body_font
                    c2.alignment = center_align
                    c2.fill = fill
                    c2.border = grid_border

                    # Col 3: Tender ID
                    c3 = ws1.cell(row=current_row, column=3, value=tid)
                    c3.font = body_font
                    c3.alignment = center_align
                    c3.fill = fill
                    c3.border = grid_border

                    # Col 4: Title
                    c4 = ws1.cell(row=current_row, column=4, value=title)
                    c4.font = body_font
                    c4.alignment = left_align
                    c4.fill = fill
                    c4.border = grid_border

                    # Col 5: Department
                    c5 = ws1.cell(row=current_row, column=5, value=dept)
                    c5.font = body_font
                    c5.alignment = left_align
                    c5.fill = fill
                    c5.border = grid_border

                    # Col 6: Published Date
                    c6 = ws1.cell(row=current_row, column=6, value=pub_date_str)
                    c6.font = body_font
                    c6.alignment = center_align
                    c6.fill = fill
                    c6.border = grid_border

                    # Col 7: Due Date
                    c7 = ws1.cell(row=current_row, column=7, value=due_date_str)
                    c7.font = bold_body_font
                    c7.alignment = center_align
                    c7.fill = fill
                    c7.border = grid_border

                    # Col 8: Status
                    c8 = ws1.cell(row=current_row, column=8, value=status_label)
                    c8.alignment = center_align
                    c8.border = grid_border
                    if "LIVE" in status_label:
                        c8.fill = live_badge_fill
                        c8.font = badge_green_font
                    elif "CLOSING" in status_label:
                        c8.fill = closing_badge_fill
                        c8.font = badge_red_font
                    else:
                        c8.fill = upcoming_badge_fill
                        c8.font = badge_blue_font

                    # Col 9: Document File Name
                    c9 = ws1.cell(row=current_row, column=9, value=fname)
                    c9.font = bold_body_font
                    c9.alignment = left_align
                    c9.fill = fill
                    c9.border = grid_border

                    # Col 10: Document Type
                    c10 = ws1.cell(row=current_row, column=10, value=doc_type)
                    c10.font = body_font
                    c10.alignment = center_align
                    c10.fill = fill
                    c10.border = grid_border

                    # Col 11: Size (KB)
                    c11 = ws1.cell(row=current_row, column=11, value=fsize if fsize else "-")
                    c11.font = body_font
                    c11.alignment = right_align
                    c11.fill = fill
                    c11.border = grid_border

                    # Col 12: Download Document Link
                    c12 = ws1.cell(row=current_row, column=12)
                    c12.value = f'=HYPERLINK("{dl_url}", "⬇ Download {fname[:24]}")'
                    c12.font = link_font
                    c12.alignment = center_align
                    c12.fill = fill
                    c12.border = grid_border

                    # Col 13: Open in App Link
                    c13 = ws1.cell(row=current_row, column=13)
                    c13.value = f'=HYPERLINK("{app_deep_link}", "🚀 Open in Portal")'
                    c13.font = link_font
                    c13.alignment = center_align
                    c13.fill = fill
                    c13.border = grid_border

                    current_row += 1
                    row_count += 1

                    # If this document has extracted sub-documents, include them as child rows!
                    sub_docs = d.get("sub_documents", [])
                    for sub_d in sub_docs:
                        sub_fname = sub_d.get("file_name", "Sub Document")
                        sub_ext = sub_d.get("file_type") or Path(sub_fname).suffix or ".pdf"
                        sub_size = sub_d.get("file_size_kb", 0)
                        sub_id = sub_d.get("id")
                        sub_lp = sub_d.get("local_path")
                        if sub_id and sub_id < 800000:
                            sub_dl = f"{base_api_url}/api/documents/download?id={sub_id}&attachment=true"
                        elif sub_lp:
                            sub_dl = f"{base_api_url}/api/documents/download?path={urllib.parse.quote(sub_lp)}&attachment=true"
                        else:
                            sub_dl = dl_url

                        ws1.row_dimensions[current_row].height = 20
                        sub_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

                        ws1.cell(row=current_row, column=1, value=sname).fill = sub_fill
                        ws1.cell(row=current_row, column=2, value=kw_name).fill = sub_fill
                        ws1.cell(row=current_row, column=3, value=f"{tid} (pkg)").fill = sub_fill
                        ws1.cell(row=current_row, column=4, value=f"↳ Part of: {fname}").fill = sub_fill
                        ws1.cell(row=current_row, column=5, value=dept).fill = sub_fill
                        ws1.cell(row=current_row, column=6, value=pub_date_str).fill = sub_fill
                        ws1.cell(row=current_row, column=7, value=due_date_str).fill = sub_fill
                        ws1.cell(row=current_row, column=8, value="📂 PACKAGE FILE").fill = sub_fill

                        c_sub_fn = ws1.cell(row=current_row, column=9, value=f"  ↳ {sub_fname}")
                        c_sub_fn.font = body_font
                        c_sub_fn.fill = sub_fill

                        ws1.cell(row=current_row, column=10, value="Section Doc").fill = sub_fill
                        ws1.cell(row=current_row, column=11, value=sub_size).fill = sub_fill

                        c_sub_dl = ws1.cell(row=current_row, column=12)
                        c_sub_dl.value = f'=HYPERLINK("{sub_dl}", "⬇ Download {sub_fname[:20]}")'
                        c_sub_dl.font = link_font
                        c_sub_dl.fill = sub_fill

                        c_sub_app = ws1.cell(row=current_row, column=13)
                        c_sub_app.value = f'=HYPERLINK("{app_deep_link}", "🚀 Open")'
                        c_sub_app.font = link_font
                        c_sub_app.fill = sub_fill

                        for col_k in range(1, 14):
                            ws1.cell(row=current_row, column=col_k).border = grid_border

                        current_row += 1
                        row_count += 1

    # Freeze top headers
    ws1.freeze_panes = "A5"

    # Auto-fit column widths
    col_widths = {
        1: 20,  # State
        2: 18,  # Keyword
        3: 24,  # Tender ID
        4: 45,  # Title
        5: 35,  # Department
        6: 15,  # Published
        7: 18,  # Due Date
        8: 18,  # Status
        9: 40,  # Document Name
        10: 18, # Type
        11: 14, # Size
        12: 32, # Download Link
        13: 22  # Open in App
    }
    for col_idx, width in col_widths.items():
        col_letter = get_column_letter(col_idx)
        ws1.column_dimensions[col_letter].width = width

    # -------------------------------------------------------------
    # SHEET 2: STATE & KEYWORD SUMMARY
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="State Summary")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:F1")
    t2 = ws2["A1"]
    t2.value = "GISFY Automated Proposals — Monitored States & Keywords Matrix"
    t2.font = title_font
    ws2.row_dimensions[1].height = 28

    s2_headers = [
        "State Name",
        "Official Portal URL",
        "Target Keywords Monitored",
        "Total Active Proposals",
        "Available Proposal Documents",
        "Launch State in Portal"
    ]
    ws2.row_dimensions[3].height = 26
    for col_idx, h in enumerate(s2_headers, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.fill = indigo_sub_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = grid_border

    s2_row = 4
    for s_idx, state in enumerate(report_data):
        sname = state.get("state_name", "")
        portal_url = state.get("portal_url") or "https://eprocure.gov.in"
        kw_list = [k["keyword"] for k in state.get("keywords", []) if k.get("tenders")]
        total_p = sum(len(k.get("tenders", [])) for k in state.get("keywords", []))
        total_d = state.get("total_docs_count", 0)
        s_app_url = f"{base_app_url}/?state={urllib.parse.quote(sname)}"

        fill2 = light_zebra_fill if s_idx % 2 == 1 else white_fill
        ws2.row_dimensions[s2_row].height = 22

        c = ws2.cell(row=s2_row, column=1, value=sname)
        c.font = bold_body_font
        c.fill = fill2
        c.border = grid_border

        c = ws2.cell(row=s2_row, column=2)
        c.value = f'=HYPERLINK("{portal_url}", "Official Portal ↗")'
        c.font = link_font
        c.fill = fill2
        c.border = grid_border

        c = ws2.cell(row=s2_row, column=3, value=", ".join(kw_list) if kw_list else "All Configured")
        c.font = body_font
        c.fill = fill2
        c.border = grid_border

        c = ws2.cell(row=s2_row, column=4, value=total_p)
        c.font = bold_body_font
        c.alignment = center_align
        c.fill = fill2
        c.border = grid_border

        c = ws2.cell(row=s2_row, column=5, value=total_d)
        c.font = bold_body_font
        c.alignment = center_align
        c.fill = fill2
        c.border = grid_border

        c = ws2.cell(row=s2_row, column=6)
        c.value = f'=HYPERLINK("{s_app_url}", "🌐 Open State Portal")'
        c.font = link_font
        c.alignment = center_align
        c.fill = fill2
        c.border = grid_border

        s2_row += 1

    ws2.freeze_panes = "A4"
    s2_col_widths = {1: 24, 2: 24, 3: 40, 4: 22, 5: 26, 6: 25}
    for col_idx, width in s2_col_widths.items():
        col_letter = get_column_letter(col_idx)
        ws2.column_dimensions[col_letter].width = width

    # Save to disk
    final_filename = output_filename or "GISFY_Proposals_And_Documents_Master.xlsx"
    out_path = STORAGE_REPORTS_DIR / final_filename
    wb.save(str(out_path))
    return out_path
