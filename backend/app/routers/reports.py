import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models

router = APIRouter()

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

@router.get("/state-keyword")
def get_state_keyword_report(db: Session = Depends(get_db)):
    states = db.query(models.State).order_by(models.State.name.asc()).all()
    all_kws = db.query(models.Keyword).filter(models.Keyword.is_active == True).all()
    report = []
    
    for state in states:
        total_docs = 0
        downloaded_docs = 0
        
        state_data = {
            "state_name": state.name,
            "portal_url": state.portal_url,
            "keywords": []
        }
        
        # Build tender objects once per tender
        state_keywords = {}
        for tender in state.tenders:
            raw_docs = []
            for d in tender.documents:
                total_docs += 1
                is_on_disk = bool(d.local_path and os.path.exists(d.local_path))
                if is_on_disk:
                    downloaded_docs += 1
                    
                size_kb = round(os.path.getsize(d.local_path) / 1024, 1) if is_on_disk else (d.portal_size_kb or 0.0)
                ext = (d.file_type or Path(d.file_name).suffix).lower()
                if not ext and "zip" in d.file_name.lower():
                    ext = ".zip"

                is_bundle = (ext == ".zip") or ("bundle" in d.file_name.lower()) or ("all_documents" in d.file_name.lower())
                is_large = bool(ext == ".pdf" and size_kb >= 1000)

                raw_docs.append({
                    "id": d.id,
                    "file_name": d.file_name,
                    "file_type": ext,
                    "local_path": d.local_path if is_on_disk else None,
                    "source_url": d.source_url or tender.portal_tender_url or state.portal_url,
                    "download_status": "downloaded" if is_on_disk else "portal_notice",
                    "verified": bool(is_on_disk),
                    "file_size_kb": size_kb,
                    "is_available": bool(is_on_disk),
                    "is_downloaded": bool(is_on_disk),
                    "is_bundle": is_bundle,
                    "is_large": is_large,
                    "is_pdf": ext == ".pdf",
                    "is_xlsx": ext in [".xls", ".xlsx"]
                })

            # Universal Document Grouping across all states and tenders
            # 1. Map existing zip archives by stem and flag duplicate internal bundles
            zip_by_stem = {}
            for doc in raw_docs:
                doc["sub_documents"] = []
                doc["is_sub_document"] = False
                fn = doc["file_name"].lower()
                doc["is_duplicate_bundle"] = (fn == "bundle_zip.zip")
                if doc["file_type"] == ".zip" and not doc["is_duplicate_bundle"]:
                    stem = Path(doc["file_name"]).stem.lower()
                    zip_by_stem[stem] = doc

            # 2. Check each document: group any file inside a subfolder under tender_id into its parent archive
            top_level_docs = []
            synthesized_zips = {}
            tender_id_str = str(tender.tender_id)

            for doc in raw_docs:
                if doc.get("is_duplicate_bundle"):
                    continue

                lp = doc.get("local_path")
                is_sub = False
                parent_zip_doc = None
                top_folder = None

                if lp:
                    parts = Path(lp).parts
                    if tender_id_str in parts:
                        t_idx = parts.index(tender_id_str)
                        if len(parts) > t_idx + 2:
                            # It is nested inside an unpacked subfolder under tender_id!
                            is_sub = True
                            top_folder = parts[t_idx + 1]

                # If it's a subfolder file, find or resolve its parent ZIP archive
                if is_sub and top_folder:
                    folder_key = top_folder.lower()
                    if folder_key in zip_by_stem:
                        parent_zip_doc = zip_by_stem[folder_key]
                    else:
                        for stem, zdoc in zip_by_stem.items():
                            if stem.startswith(folder_key) or folder_key.startswith(stem):
                                parent_zip_doc = zdoc
                                break

                    # If no existing zip was in raw_docs, check disk in tender root or synthesize it
                    if not parent_zip_doc:
                        if folder_key not in synthesized_zips:
                            disk_zip_path = None
                            if lp:
                                tender_dir = Path(*Path(lp).parts[:parts.index(tender_id_str) + 1])
                                if tender_dir.exists():
                                    for f in tender_dir.iterdir():
                                        if f.is_file() and f.suffix.lower() == ".zip" and ("all_documents" not in f.name.lower()):
                                            if f.stem.lower() == folder_key or f.stem.lower().startswith(folder_key) or folder_key.startswith(f.stem.lower()):
                                                disk_zip_path = str(f)
                                                break
                            zip_name = Path(disk_zip_path).name if disk_zip_path else f"{top_folder}.zip"
                            size_kb = round(os.path.getsize(disk_zip_path) / 1024, 1) if (disk_zip_path and os.path.exists(disk_zip_path)) else 45.0
                            synthesized_zips[folder_key] = {
                                "id": 800000 + abs(hash(f"{tender.id}-{top_folder}")) % 100000,
                                "file_name": zip_name,
                                "file_type": ".zip",
                                "local_path": disk_zip_path,
                                "source_url": tender.portal_tender_url or state.portal_url,
                                "download_status": "downloaded" if disk_zip_path else "ready",
                                "verified": bool(disk_zip_path),
                                "file_size_kb": size_kb,
                                "is_available": True,
                                "is_downloaded": bool(disk_zip_path),
                                "is_bundle": False,
                                "is_portal_zip": True,
                                "is_archive": True,
                                "is_large": False,
                                "is_pdf": False,
                                "is_xlsx": False,
                                "sub_documents": []
                            }
                        parent_zip_doc = synthesized_zips[folder_key]

                    doc["is_sub_document"] = True
                    doc["parent_archive"] = parent_zip_doc["file_name"]
                    parent_zip_doc["sub_documents"].append(doc)
                    continue

                # 3. Check if it's a docx/xlsx/pdf matching a zip stem sitting directly in root
                if not is_sub and doc["file_type"] in (".docx", ".xlsx", ".doc", ".pdf"):
                    stem = Path(doc["file_name"]).stem.lower()
                    if stem in zip_by_stem and zip_by_stem[stem] is not doc:
                        parent_zip_doc = zip_by_stem[stem]
                        doc["is_sub_document"] = True
                        doc["parent_archive"] = parent_zip_doc["file_name"]
                        parent_zip_doc["sub_documents"].append(doc)
                        continue

                top_level_docs.append(doc)

            # Include any synthesized archives that collected extracted sub-documents
            for syn_zip in synthesized_zips.values():
                if syn_zip not in top_level_docs:
                    top_level_docs.append(syn_zip)

            # Separate individual non-bundle documents from compressed ZIP archives
            individual_docs = [doc for doc in top_level_docs if doc["file_type"] != ".zip"]
            bundle_docs = [doc for doc in top_level_docs if doc["file_type"] == ".zip"]

            # Locate or generate main comprehensive bundle for this tender
            main_bundle_name = f"Tender_{tender.tender_id}_All_Documents.zip"
            main_bundle = None

            for b in bundle_docs:
                fn = b["file_name"].lower()
                if "all_documents" in fn:
                    main_bundle = b
                    b["is_bundle"] = True
                    b["is_all_in_one"] = True
                    break

            if not main_bundle and individual_docs:
                bundle_path = None
                if individual_docs[0].get("local_path"):
                    p = Path(individual_docs[0]["local_path"]).parent / main_bundle_name
                    if p.exists():
                        bundle_path = str(p)
                size_kb = round(os.path.getsize(bundle_path) / 1024, 1) if (bundle_path and os.path.exists(bundle_path)) else 45.0
                main_bundle = {
                    "id": 900000 + tender.id,
                    "file_name": main_bundle_name,
                    "file_type": ".zip",
                    "local_path": bundle_path,
                    "source_url": tender.portal_tender_url or state.portal_url,
                    "download_status": "downloaded" if bundle_path else "ready",
                    "verified": bool(bundle_path),
                    "file_size_kb": size_kb,
                    "is_available": True,
                    "is_downloaded": bool(bundle_path),
                    "is_bundle": True,
                    "is_all_in_one": True,
                    "is_large": False,
                    "is_pdf": False,
                    "is_xlsx": False,
                    "sub_documents": []
                }
                bundle_docs.append(main_bundle)

            # Sub-bundles that are official portal ZIP archives (not the artificial all-in-one bundle)
            sub_bundles = [b for b in bundle_docs if b is not main_bundle]
            for b in sub_bundles:
                b["is_bundle"] = False
                b["is_portal_zip"] = True
                b["is_archive"] = True

            if main_bundle:
                main_bundle["is_bundle"] = True
                main_bundle["is_all_in_one"] = True

            # Annotate all archives with their sub-documents count
            for b in bundle_docs:
                b["sub_documents_count"] = len(b.get("sub_documents", []))

            # Annotate main bundle with file count and metadata
            if main_bundle:
                total_files_in_tender = len(individual_docs) + sum(len(b.get("sub_documents", [])) for b in sub_bundles)
                main_bundle["bundle_file_count"] = total_files_in_tender
                main_bundle["bundle_label"] = f"All-in-One Compressed Archive ({total_files_in_tender} Files)"
                main_bundle["bundle_description"] = f"Complete compressed package containing all documents of Tender #{tender.tender_id}."

            # Top-level portal files first (PDFs/spreadsheets/portal zips), and all-in-one ZIP at the end!
            docs = individual_docs + sub_bundles + ([main_bundle] if main_bundle else [])

            now = datetime.utcnow()
            stage = "live"
            days_left = None
            if tender.published_date and tender.published_date > now:
                stage = "upcoming"
                days_left = max(0, (tender.published_date - now).days)
            elif tender.last_date:
                diff_days = (tender.last_date - now).days
                if diff_days < 0:
                    stage = "closed"
                    days_left = 0
                elif diff_days <= 3:
                    stage = "closing_soon"
                    days_left = diff_days
                else:
                    stage = "live"
                    days_left = diff_days

            t_obj = {
                "id": tender.id,
                "tender_id": tender.tender_id,
                "title": tender.title,
                "department": tender.department,
                "published_date": tender.published_date.isoformat() if tender.published_date else None,
                "published_date_formatted": tender.published_date.strftime("%d %b %Y") if tender.published_date else None,
                "last_date": tender.last_date.isoformat() if tender.last_date else None,
                "last_date_formatted": tender.last_date.strftime("%d %b %Y") if tender.last_date else None,
                "status": tender.status,
                "stage": stage,
                "days_left": days_left,
                "is_live": stage in ("live", "closing_soon"),
                "is_upcoming": stage == "upcoming",
                "is_closing_soon": stage == "closing_soon",
                "description": tender.description,
                "portal_tender_url": tender.portal_tender_url or state.portal_url,
                "documents": docs
            }

            for kw in tender.keywords:
                if kw.keyword not in state_keywords:
                    state_keywords[kw.keyword] = []
                state_keywords[kw.keyword].append(t_obj)
        
        # Ensure all active keywords are listed
        for kw in all_kws:
            if kw.keyword in state_keywords:
                state_data["keywords"].append({
                    "keyword": kw.keyword,
                    "tenders": state_keywords[kw.keyword]
                })
            else:
                state_data["keywords"].append({
                    "keyword": kw.keyword,
                    "tenders": []
                })
            
        state_data["total_docs_count"] = total_docs
        state_data["downloaded_docs_count"] = downloaded_docs
        report.append(state_data)

    # Arrange all states in alphabetical order (A to Z)
    report.sort(key=lambda s: s["state_name"].lower())

    return report


@router.get("/proposals-excel")
def download_proposals_excel(db: Session = Depends(get_db)):
    """Generate and return master proposals & documents Excel spreadsheet (.xlsx)."""
    from app.services.excel_service import generate_proposals_excel
    report_data = get_state_keyword_report(db)
    excel_path = generate_proposals_excel(report_data=report_data)

    if not excel_path or not excel_path.exists():
        raise HTTPException(status_code=500, detail="Failed to generate Excel file.")

    headers = {
        "Content-Disposition": 'attachment; filename="GISFY_Proposals_And_Documents_Master.xlsx"',
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Expose-Headers": "Content-Disposition"
    }
    return FileResponse(
        str(excel_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="GISFY_Proposals_And_Documents_Master.xlsx",
        headers=headers
    )


@router.get("/excel-view", response_class=HTMLResponse)
def view_proposals_excel_table(
    state: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Renders an interactive, responsive Excel-style spreadsheet in the browser.
    Allows searching, filtering by state & keyword, and downloading every proposal document with one click.
    """
    report_data = get_state_keyword_report(db)
    
    # Filter if query parameters provided
    if state:
        report_data = [s for s in report_data if s["state_name"].lower() == state.lower()]

    rows_html = ""
    row_count = 0
    total_docs = 0

    all_states = sorted(list(set(s["state_name"] for s in report_data)))
    all_kws = set()

    for s in report_data:
        sname = s["state_name"]
        portal_url = s.get("portal_url") or "https://eprocure.gov.in"
        for kw_item in s.get("keywords", []):
            kw_name = kw_item.get("keyword", "")
            if keyword and kw_name.lower() != keyword.lower():
                continue
            all_kws.add(kw_name)
            tenders = kw_item.get("tenders", [])
            for t in tenders:
                tid = t.get("tender_id")
                title = t.get("title", "")
                dept = t.get("department", "State Agency")
                due = format_dmy(t.get("last_date"))
                stage = t.get("stage", "live")
                badge_class = "badge-live" if stage == "live" else ("badge-closing" if stage == "closing_soon" else "badge-upcoming")
                badge_label = "LIVE" if stage == "live" else ("CLOSING SOON" if stage == "closing_soon" else "UPCOMING")

                app_link = f"http://localhost:5173/?state={urllib.parse.quote(sname)}&keyword={urllib.parse.quote(kw_name)}&tender={urllib.parse.quote(str(tid))}"
                docs = t.get("documents", [])
                
                if not docs:
                    docs = [{"file_name": "Portal Notice", "file_type": ".pdf", "file_size_kb": 0, "id": None, "local_path": None}]

                for d in docs:
                    fname = d.get("file_name", "Document")
                    fsize = f"{d.get('file_size_kb', 0)} KB" if d.get('file_size_kb') else "-"
                    is_zip = fname.lower().endswith(".zip")
                    doc_id_param = f"id={d.get('id', '')}" if (d.get('id') and d.get('id') < 800000) else f"path={urllib.parse.quote(d.get('local_path') or '')}"
                    dl_url = f"/api/documents/download?{doc_id_param}&attachment=true" if (d.get('id') or d.get('local_path')) else portal_url
                    
                    row_bg = "background: #f8fafc;" if row_count % 2 == 1 else "background: #ffffff;"
                    total_docs += 1
                    row_count += 1

                    rows_html += f"""
                    <tr style="{row_bg}">
                        <td style="font-weight: 700; color: #1e293b;">{sname}</td>
                        <td style="text-align: center;"><span class="kw-tag">{kw_name}</span></td>
                        <td style="font-family: monospace; font-size: 11px; color: #475569;">#{tid}</td>
                        <td style="color: #0f172a; max-width: 320px; line-height: 1.3;">{title}</td>
                        <td style="color: #64748b; font-size: 12px;">{dept}</td>
                        <td style="text-align: center; font-weight: 600; color: #b91c1c;">{due}</td>
                        <td style="text-align: center;"><span class="{badge_class}">{badge_label}</span></td>
                        <td style="font-weight: 600; color: #334155; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            {"📦 " if is_zip else "📄 "}{fname}
                        </td>
                        <td style="text-align: right; color: #64748b; font-size: 11px;">{fsize}</td>
                        <td style="text-align: center;">
                            <a href="{dl_url}" class="btn-dl" target="_blank">⬇ Download</a>
                        </td>
                        <td style="text-align: center;">
                            <a href="{app_link}" class="btn-app" target="_blank">🚀 Open</a>
                        </td>
                    </tr>
                    """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GISFY Proposals &amp; Documents — Interactive Spreadsheet</title>
        <style>
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }}
            .header {{
                background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
                color: #ffffff;
                padding: 20px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; }}
            .header p {{ margin: 0; font-size: 13px; opacity: 0.9; color: #c7d2fe; }}
            .actions {{ display: flex; gap: 12px; }}
            .btn-excel {{
                background: #10b981;
                color: #ffffff;
                text-decoration: none;
                padding: 10px 18px;
                border-radius: 8px;
                font-weight: 700;
                font-size: 13px;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 2px 6px rgba(16,185,129,0.3);
            }}
            .btn-excel:hover {{ background: #059669; }}
            .btn-portal {{
                background: rgba(255,255,255,0.15);
                border: 1px solid rgba(255,255,255,0.3);
                color: #ffffff;
                text-decoration: none;
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            .btn-portal:hover {{ background: rgba(255,255,255,0.25); }}
            .toolbar {{
                background: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                padding: 12px 30px;
                display: flex;
                gap: 16px;
                align-items: center;
                flex-wrap: wrap;
            }}
            .search-input {{
                padding: 8px 14px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
                width: 280px;
                outline: none;
            }}
            .search-input:focus {{ border-color: #4f46e5; ring: 2px solid #e0e7ff; }}
            .stats-chip {{
                background: #eef2ff;
                color: #4338ca;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                border: 1px solid #c7d2fe;
            }}
            .table-container {{
                padding: 20px 30px;
                overflow-x: auto;
                max-height: calc(100vh - 160px);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
                font-size: 12px;
            }}
            th {{
                background: #1e1b4b;
                color: #ffffff;
                text-align: left;
                padding: 12px 14px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                position: sticky;
                top: 0;
                z-index: 10;
            }}
            td {{
                padding: 10px 14px;
                border-bottom: 1px solid #e2e8f0;
                vertical-align: middle;
            }}
            .kw-tag {{
                display: inline-block;
                padding: 3px 8px;
                background: #e0e7ff;
                color: #4338ca;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
            }}
            .badge-live {{
                display: inline-block;
                padding: 3px 8px;
                background: #dcfce7;
                color: #15803d;
                border-radius: 6px;
                font-weight: 700;
                font-size: 10px;
            }}
            .badge-closing {{
                display: inline-block;
                padding: 3px 8px;
                background: #fee2e2;
                color: #b91c1c;
                border-radius: 6px;
                font-weight: 700;
                font-size: 10px;
            }}
            .badge-upcoming {{
                display: inline-block;
                padding: 3px 8px;
                background: #eff6ff;
                color: #1d4ed8;
                border-radius: 6px;
                font-weight: 700;
                font-size: 10px;
            }}
            .btn-dl {{
                display: inline-block;
                padding: 5px 12px;
                background: #4f46e5;
                color: #ffffff;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                white-space: nowrap;
            }}
            .btn-dl:hover {{ background: #4338ca; }}
            .btn-app {{
                display: inline-block;
                padding: 5px 10px;
                background: #f1f5f9;
                color: #334155;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                white-space: nowrap;
            }}
            .btn-app:hover {{ background: #e2e8f0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>📊 GISFY Proposals &amp; Documents Master Spreadsheet</h1>
                <p>Interactive table view of all states, keywords, proposals, and attached authentic portal files</p>
            </div>
            <div class="actions">
                <a href="/api/reports/proposals-excel" class="btn-excel">
                    📥 Download Excel File (.xlsx)
                </a>
                <a href="http://localhost:5173" class="btn-portal">
                    🚀 Launch Full Web App ↗
                </a>
            </div>
        </div>

        <div class="toolbar">
            <input type="text" id="filterInput" class="search-input" placeholder="🔍 Quick search state, keyword, or document..." onkeyup="filterTable()">
            <div class="stats-chip">
                📋 Total Rows: <b>{row_count}</b>
            </div>
            <div class="stats-chip" style="background: #ecfdf5; color: #047857; border-color: #a7f3d0;">
                📑 Total Documents: <b>{total_docs}</b>
            </div>
            <div style="font-size: 12px; color: #64748b; margin-left: auto;">
                💡 <i>Click 'Download' on any row to immediately save the authentic document to your computer.</i>
            </div>
        </div>

        <div class="table-container">
            <table id="proposalsTable">
                <thead>
                    <tr>
                        <th>State</th>
                        <th style="text-align: center;">Keyword</th>
                        <th>Tender ID</th>
                        <th>Proposal Title</th>
                        <th>Department</th>
                        <th style="text-align: center;">Due Date</th>
                        <th style="text-align: center;">Status</th>
                        <th>Attached Document</th>
                        <th style="text-align: right;">Size</th>
                        <th style="text-align: center;">Document Download</th>
                        <th style="text-align: center;">Web Portal</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <script>
            function filterTable() {{
                const input = document.getElementById("filterInput").value.toLowerCase();
                const table = document.getElementById("proposalsTable");
                const tr = table.getElementsByTagName("tr");
                for (let i = 1; i < tr.length; i++) {{
                    const text = tr[i].textContent.toLowerCase();
                    tr[i].style.display = text.includes(input) ? "" : "none";
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/download-codebase-zip")
def download_codebase_zip():
    """Serve the complete codebase ZIP archive for sharing with developers."""
    zip_path = Path("/Users/gisfymac3/Desktop/Automated Proposals/GISFY_Automated_Proposals_Full_Codebase.zip")
    if not zip_path.exists():
        raise HTTPException(
            status_code=404, 
            detail="Codebase ZIP is currently being finalized. Please refresh in a moment."
        )

    headers = {
        "Content-Disposition": 'attachment; filename="GISFY_Automated_Proposals_Full_Codebase.zip"',
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Expose-Headers": "Content-Disposition"
    }
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename="GISFY_Automated_Proposals_Full_Codebase.zip",
        headers=headers
    )



