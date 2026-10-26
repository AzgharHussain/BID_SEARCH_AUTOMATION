import os
from io import BytesIO
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session
from app.models import models

def generate_collaboration_excel_workbook(db: Session) -> BytesIO:
    """Generate a comprehensive Excel tracking workbook of all partner collaboration emails."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Partner Outreach Tracker"
    ws.views.sheetView[0].showGridLines = True

    # Palette
    NAVY_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    HEADER_FILL = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    SUB_FILL = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    
    STATUS_FILLS = {
        "sent": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),       # light green
        "replied": PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid"),    # yellow
        "approved": PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),   # blue
        "draft": PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid"),      # gray
        "failed": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid"),     # red
        "opted_out": PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid")  # purple
    }

    WHITE_BOLD = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    TITLE_FONT = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
    BOLD_FONT = Font(name="Segoe UI", size=10, bold=True, color="0F172A")
    REG_FONT = Font(name="Segoe UI", size=10, color="334155")
    MUTED_FONT = Font(name="Segoe UI", size=9, color="64748B")

    THIN_BORDER = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    # Title Banner
    ws.merge_cells("A1:T1")
    title_cell = ws["A1"]
    title_cell.value = "GISFY PRIVATE LIMITED – TENDER-BASED PARTNER COLLABORATION EMAIL TRACKER"
    title_cell.font = TITLE_FONT
    title_cell.fill = NAVY_FILL
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 42

    # Subtitle
    ws.merge_cells("A2:T2")
    sub_cell = ws["A2"]
    sub_cell.value = f"Automated Daily 9:00 AM IST Outreach Pipeline | Generated: {datetime.utcnow().strftime('%d %b %Y %H:%M UTC')} | Confidential"
    sub_cell.font = Font(name="Segoe UI", size=10, italic=True, color="E2E8F0")
    sub_cell.fill = HEADER_FILL
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 24

    # Headers
    headers = [
        "Record ID",
        "Tender ID",
        "Project Title",
        "State",
        "Bid Deadline",
        "Partner Company",
        "Contact Person",
        "Verified Email",
        "Match Score",
        "Synergy & Rationale",
        "Workflow Status",
        "Approval Status",
        "Draft Created",
        "Approved At",
        "Sent At",
        "Follow-up Due",
        "Response Status",
        "Reply Received",
        "Response Notes",
        "Gmail Message ID"
    ]

    ws.row_dimensions[4].height = 28
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        cell.font = WHITE_BOLD
        cell.fill = SUB_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER

    # Query all emails
    records = db.query(models.CollaborationEmail).order_by(models.CollaborationEmail.id.desc()).all()

    current_row = 5
    for r in records:
        tender = r.tender
        state_name = tender.state.name if (tender and tender.state) else "-"
        deadline_str = tender.last_date.strftime("%d %b %Y") if (tender and tender.last_date) else "-"
        created_str = r.created_at.strftime("%d %b %Y %H:%M") if r.created_at else "-"
        approved_str = r.approved_at.strftime("%d %b %Y %H:%M") if r.approved_at else "-"
        sent_str = r.sent_at.strftime("%d %b %Y %H:%M") if r.sent_at else "-"
        follow_str = r.follow_up_date.strftime("%d %b %Y") if r.follow_up_date else "-"
        replied_str = r.response_received_at.strftime("%d %b %Y %H:%M") if r.response_received_at else "-"

        row_data = [
            f"OUT-{r.id:04d}",
            tender.tender_id if tender else "-",
            (tender.title[:75] + "...") if (tender and tender.title and len(tender.title) > 75) else (tender.title if tender else "-"),
            state_name,
            deadline_str,
            r.company_name,
            r.recipient_name or "-",
            r.recipient_email,
            f"{r.match_score:.1f}%",
            r.selection_reason or "-",
            r.status.upper(),
            r.approval_status.replace("_", " ").title(),
            created_str,
            approved_str,
            sent_str,
            follow_str,
            r.response_status.title(),
            replied_str,
            r.response_snippet or (r.last_error if r.status == "failed" else "-"),
            r.gmail_message_id or r.gmail_draft_id or "-"
        ]

        ws.row_dimensions[current_row].height = 22
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=val)
            cell.font = REG_FONT
            cell.border = THIN_BORDER
            
            # Alignments
            if col_idx in [1, 2, 4, 5, 9, 11, 12, 13, 14, 15, 16, 17, 18]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

            # Status cell styling
            if col_idx == 11:
                status_key = r.status.lower()
                if status_key in STATUS_FILLS:
                    cell.fill = STATUS_FILLS[status_key]
                    cell.font = BOLD_FONT

        current_row += 1

    # If no records exist yet, add sample row
    if not records:
        ws.row_dimensions[5].height = 24
        sample_cell = ws.cell(row=5, column=1, value="No partner collaboration emails generated yet. Use the 'Generate Drafts' button in dashboard.")
        sample_cell.font = MUTED_FONT
        ws.merge_cells("A5:T5")
        sample_cell.alignment = Alignment(horizontal="center", vertical="center")

    # Auto-adjust column widths
    min_widths = {
        1: 12, 2: 18, 3: 35, 4: 16, 5: 14, 6: 28, 7: 24, 8: 30, 9: 13, 10: 36,
        11: 16, 12: 18, 13: 18, 14: 18, 15: 18, 16: 15, 17: 16, 18: 18, 19: 30, 20: 22
    }
    for col_idx, width in min_widths.items():
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
