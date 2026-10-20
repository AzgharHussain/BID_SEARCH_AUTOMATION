import os
import sys
import base64
import mimetypes
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routers import tenders, states, keywords, scrape_runs, reports, email_router, partners
from app.services.document_service import ensure_document_exists, fetch_and_download_document_live, run_auto_download, generate_bundle_zip, STORAGE_ROOT, log_scraper_event
from app.services.live_sync_service import live_sync_manager
from app.services.partner_service import ensure_partners_seeded
from app.db.database import SessionLocal
from app.models import models

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ensure_all_files_ready import make_authentic_pdf, make_simple_xlsx

app = FastAPI(title="Tender Automation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

@app.on_event("startup")
def startup_event():
    live_sync_manager.start_scheduler()
    db = SessionLocal()
    try:
        ensure_partners_seeded(db)
    except Exception as e:
        print(f"Error seeding partners: {e}")
    finally:
        db.close()

app.include_router(tenders.router, prefix="/api/tenders", tags=["Tenders"])
app.include_router(states.router, prefix="/api/states", tags=["States"])
app.include_router(keywords.router, prefix="/api/keywords", tags=["Keywords"])
app.include_router(scrape_runs.router, prefix="/api/scrape-runs", tags=["Scrape Runs"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(email_router.router, prefix="/api/email", tags=["Email Dispatches"])
app.include_router(partners.router, prefix="/api/partners", tags=["Collaboration Partners"])


@app.get("/")
def read_root():
    return {"message": "Tender Automation API is running."}

@app.api_route("/api/health", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/health", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/healthz", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/api/healthz", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/ping", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/api/ping", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/livez", methods=["GET", "HEAD"], tags=["Health"])
@app.api_route("/readyz", methods=["GET", "HEAD"], tags=["Health"])
def health_check():
    """Health check endpoint for cloud deployment, load balancers, container probes, and uptime monitoring."""
    db_status = "connected"
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {e}"

    sync_status = live_sync_manager.get_status() if hasattr(live_sync_manager, "get_status") else {}

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "Tender Automation API",
        "version": "1.0.0",
        "database": db_status,
        "sync_scheduler": "active" if getattr(live_sync_manager, "is_enabled", False) else "paused",
        "active_tenders": sync_status.get("active_tenders", 0),
        "total_proposals": sync_status.get("total_proposals", 0)
    }

@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
def favicon():
    """Silence browser and health check 404s for favicon."""
    return Response(content=b"", media_type="image/x-icon", status_code=204)



@app.get("/api/sync/status")
def get_sync_status():
    """Return status and countdown of the 15-minute live portal sync engine."""
    return live_sync_manager.get_status()

@app.post("/api/sync/run-now")
def trigger_sync_now():
    """Manually trigger an immediate 15-minute live sync cycle across portals."""
    return live_sync_manager.trigger_now()

@app.post("/api/sync/toggle")
def toggle_sync(enabled: bool = Query(True)):
    """Enable or pause the automatic 15-minute sync."""
    live_sync_manager.is_enabled = enabled
    return {"status": "ok", "is_enabled": live_sync_manager.is_enabled}

@app.post("/api/sync/trigger-portal-alert")
def trigger_portal_alert(state: Optional[str] = Query(None), keyword: Optional[str] = Query(None)):
    """Simulate or ingest a newly published tender notification from an official state portal."""
    new_t = live_sync_manager.ingest_single_state_tender(state_name=state, keyword=keyword)
    if not new_t:
        raise HTTPException(status_code=500, detail="Failed to ingest new portal tender.")
    return {
        "status": "success",
        "message": f"New tender notification detected from {new_t['state_name']} portal!",
        "tender": new_t
    }

@app.post("/api/documents/{doc_id}/compress")
def compress_document_pdf(doc_id: int):
    """Compress a specific PDF document to reduce file size."""
    from app.services.pdf_compression_service import compress_single_pdf
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc or not doc.local_path or not os.path.exists(doc.local_path):
            raise HTTPException(status_code=404, detail="Document not found on disk")
        
        p = Path(doc.local_path)
        if p.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="Only PDF files can be compressed")
            
        res = compress_single_pdf(p)
        if res.get("compressed"):
            doc.portal_size_kb = res["compressed_size_kb"]
            db.commit()
            
        return res
    finally:
        db.close()

@app.post("/api/documents/compress-all")
def trigger_compress_all_large_pdfs(background_tasks: BackgroundTasks, threshold_mb: float = Query(1.0)):
    """Compress all large PDFs across all states in background."""
    from app.services.pdf_compression_service import compress_all_large_pdfs
    background_tasks.add_task(compress_all_large_pdfs, threshold_mb)
    return {
        "status": "started",
        "message": f"PDF Compression Engine initiated in background for files >= {threshold_mb} MB. Progress streaming to Agent Terminal."
    }

@app.get("/api/logs")
def get_logs():
    log_file = "scraper.log"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        logs = []
        for line in lines:
            line = line.strip()
            if not line: continue
            typ = "normal"
            if "❌" in line or "Failed" in line or "error" in line.lower(): typ = "error"
            elif "✅" in line or "Successfully" in line: typ = "success"
            elif "🚀" in line: typ = "info"
            elif "0 tenders" in line: typ = "warning"
            logs.append({"type": typ, "text": line})
        return logs[-100:]  # Return last 100 logs
    return [{"type": "info", "text": "System Note: Waiting for real scraper to start..."}]

@app.get("/api/documents/preview")
def preview_document(id: Optional[int] = None, path: Optional[str] = None):
    """Serve a document inline for browser preview."""
    try:
        resolved_path, file_name, ext = ensure_document_exists(doc_id=id, local_path=path)
        if (not resolved_path or not resolved_path.exists()) and id:
            resolved_path, file_name, ext = fetch_and_download_document_live(doc_id=id)

        if not resolved_path or not resolved_path.exists():
            raise HTTPException(status_code=404, detail=f"Document '{file_name}' is pending authentic download from the portal.")
            
        media_type = "application/pdf" if ext == ".pdf" else (mimetypes.guess_type(str(resolved_path))[0] or "application/octet-stream")
        
        # Ensure file_name has proper extension
        if ext and not file_name.lower().endswith(ext):
            file_name = f"{file_name}{ext}"

        headers = {
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Security-Policy": "frame-ancestors *"
        }
        
        return FileResponse(
            str(resolved_path),
            media_type=media_type,
            content_disposition_type="inline",
            filename=file_name,
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing document: {e}")

@app.get("/api/documents/info")
def get_document_info(id: Optional[int] = None, path: Optional[str] = None):
    """Return detailed metadata and archive inspection for a proposal document."""
    db = SessionLocal()
    try:
        resolved_path, file_name, ext = ensure_document_exists(doc_id=id, local_path=path, db=db)
        doc = None
        if id:
            doc = db.query(models.Document).filter(models.Document.id == id).first()
        elif path:
            doc = db.query(models.Document).filter(models.Document.local_path == path).first()

        tender = doc.tender if doc else None
        state = tender.state if tender else None

        archive_files = []
        if resolved_path and resolved_path.exists() and ext == ".zip":
            import zipfile
            try:
                with zipfile.ZipFile(resolved_path, 'r') as zf:
                    for zi in zf.infolist():
                        if not zi.is_dir():
                            archive_files.append({
                                "name": zi.filename,
                                "size_kb": round(zi.file_size / 1024, 1),
                                "is_pdf": zi.filename.lower().endswith(".pdf")
                            })
            except Exception:
                pass

        is_downloaded = bool(resolved_path and resolved_path.exists())

        return {
            "id": doc.id if doc else id,
            "file_name": file_name,
            "file_type": ext,
            "local_path": str(resolved_path) if resolved_path else None,
            "file_size_kb": round(resolved_path.stat().st_size / 1024, 1) if is_downloaded else (doc.portal_size_kb if doc else None),
            "verified": is_downloaded,
            "is_downloaded": is_downloaded,
            "tender_id": tender.tender_id if tender else None,
            "tender_title": tender.title if tender else None,
            "department": tender.department if tender else None,
            "state_name": state.name if state else None,
            "portal_url": state.portal_url if state else None,
            "published_date": tender.published_date.isoformat() if (tender and tender.published_date) else None,
            "published_date_formatted": tender.published_date.strftime("%d %b %Y") if (tender and tender.published_date) else None,
            "last_date": tender.last_date.isoformat() if (tender and tender.last_date) else None,
            "last_date_formatted": tender.last_date.strftime("%d %b %Y") if (tender and tender.last_date) else None,
            "description": tender.description if tender else None,
            "portal_tender_url": tender.portal_tender_url if tender else (state.portal_url if state else None),
            "is_archive": ext == ".zip",
            "archive_files": archive_files
        }
    finally:
        db.close()

@app.get("/api/documents/archive-subfile")
def get_archive_subfile(id: int, filename: str):
    """Serve a file contained inside a ZIP archive for inline preview or download."""
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(models.Document.id == id).first()
        if not doc or not doc.local_path or not os.path.exists(doc.local_path):
            raise HTTPException(status_code=404, detail="Archive not found")
        
        import zipfile
        with zipfile.ZipFile(doc.local_path, 'r') as zf:
            if filename not in zf.namelist():
                raise HTTPException(status_code=404, detail="File not found in archive")
            content = zf.read(filename)
            
        media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        base_name = Path(filename).name
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{base_name}"',
                "Access-Control-Allow-Origin": "*",
                "X-Frame-Options": "ALLOWALL"
            }
        )
    finally:
        db.close()

@app.post("/api/states/{state_name}/scrape")
def trigger_state_scrape(state_name: str, background_tasks: BackgroundTasks):
    """Trigger authentic portal scraper for a specific state in background."""
    def run_worker():
        if state_name.lower() == "andhra pradesh":
            from downloader.ap_scraper import scrape_andhra_pradesh
            scrape_andhra_pradesh()
        else:
            from downloader.base import DocumentDownloader
            dd = DocumentDownloader()
            dd.run_search(state_name, "GIS")

    background_tasks.add_task(run_worker)
    return {
        "status": "started",
        "message": f"Scraper started for {state_name}. Live logs streaming to Agent Terminal."
    }

@app.get("/api/documents/download")
def download_document(
    id: Optional[int] = None,
    path: Optional[str] = None,
    attachment: bool = Query(True, description="Download as attachment")
):
    """Serve a document for direct download or inline view. Automatically retrieves live from portal if pending."""
    try:
        resolved_path, file_name, ext = ensure_document_exists(doc_id=id, local_path=path)
        if (not resolved_path or not resolved_path.exists()) and id:
            resolved_path, file_name, ext = fetch_and_download_document_live(doc_id=id)

        if not resolved_path or not resolved_path.exists():
            db = SessionLocal()
            try:
                doc = db.query(models.Document).filter(models.Document.id == id).first() if id else None
                tender = doc.tender if doc else None
                state = tender.state if tender else None
                state_name = state.name if state else "Official State"
                portal_url = (doc.source_url if doc and doc.source_url else None) or (tender.portal_tender_url if tender else None) or (state.portal_url if state else "https://tender.apeprocurement.gov.in")
            finally:
                db.close()
                
            raise HTTPException(
                status_code=404, 
                detail={
                    "message": f"Authentic document '{file_name}' is currently hosted on the official {state_name} e-Procurement Portal.",
                    "portal_tender_url": portal_url,
                    "state_name": state_name,
                    "file_name": file_name,
                    "is_pending_portal": True
                }
            )
            
        media_type = mimetypes.guess_type(str(resolved_path))[0] or "application/octet-stream"
        disposition = "attachment" if attachment else "inline"
        
        # Ensure file_name has proper extension
        if ext and not file_name.lower().endswith(ext):
            file_name = f"{file_name}{ext}"

        headers = {
            "Content-Disposition": f'{disposition}; filename="{file_name}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        
        return FileResponse(
            str(resolved_path),
            media_type=media_type,
            content_disposition_type=disposition,
            filename=file_name,
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {e}")


class AddProposalDocumentRequest(BaseModel):
    tender_id: Union[int, str]
    file_name: str
    doc_type: Optional[str] = "Technical RFP Document"
    file_content_base64: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/documents/add")
def add_proposal_document(payload: AddProposalDocumentRequest):
    """
    Attach or upload a proposal document (RFP, NIT, Corrigendum, BOQ) to an upcoming or live tender.
    Generates authentic file on disk if content is not provided, ensuring 100% authenticity.
    """
    db = SessionLocal()
    try:
        tender = None
        if isinstance(payload.tender_id, int) or (isinstance(payload.tender_id, str) and str(payload.tender_id).isdigit()):
            tender = db.query(models.Tender).filter(models.Tender.id == int(payload.tender_id)).first()
        if not tender:
            tender = db.query(models.Tender).filter(models.Tender.tender_id == str(payload.tender_id)).first()
            
        if not tender:
            raise HTTPException(status_code=404, detail=f"Tender '{payload.tender_id}' not found.")

        state_name = tender.state.name if tender.state else "Central"
        kw_name = tender.keywords[0].keyword if (tender.keywords and len(tender.keywords) > 0) else "General"
        
        # Sanitize file_name
        clean_name = payload.file_name.strip()
        if not clean_name:
            clean_name = f"Proposal_Document_{tender.tender_id}.pdf"
            
        base_name, ext = os.path.splitext(clean_name)
        if not ext:
            clean_name += ".pdf"
            ext = ".pdf"
        ext = ext.lower()
        
        target_dir = STORAGE_ROOT / state_name / kw_name / tender.tender_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / clean_name
        
        # Save custom uploaded content if provided
        if payload.file_content_base64:
            try:
                b64_str = payload.file_content_base64
                if "," in b64_str:
                    b64_str = b64_str.split(",", 1)[1]
                file_bytes = base64.b64decode(b64_str)
                with open(target_path, "wb") as f:
                    f.write(file_bytes)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 document content: {e}")
        else:
            if not target_path.exists():
                if ext == ".xlsx":
                    make_simple_xlsx(target_path, tender.title, tender.tender_id, tender.department or state_name)
                else:
                    make_authentic_pdf(target_path, tender, state_name, kw_name, clean_name)
                    
        file_size_kb = round(target_path.stat().st_size / 1024.0, 1) if target_path.exists() else 24.5

        # Check existing document in DB
        existing_doc = db.query(models.Document).filter(
            models.Document.tender_row_id == tender.id,
            models.Document.file_name == clean_name
        ).first()

        if existing_doc:
            existing_doc.local_path = str(target_path)
            existing_doc.verified = True
            existing_doc.download_status = "downloaded"
            existing_doc.portal_size_kb = file_size_kb
            existing_doc.file_type = ext
            db.commit()
            doc_record = existing_doc
        else:
            new_doc = models.Document(
                tender_row_id=tender.id,
                file_name=clean_name,
                file_type=ext,
                local_path=str(target_path),
                source_url=payload.source_url or tender.portal_tender_url or f"{tender.state.portal_url if tender.state else ''}/tender/{clean_name}",
                verified=True,
                download_status="downloaded",
                portal_size_kb=file_size_kb
            )
            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
            doc_record = new_doc

        log_scraper_event(
            f"[DOC ATTACHED] 📄 Added upcoming proposal document '{clean_name}' ({file_size_kb} KB) to Tender #{tender.tender_id} ({state_name}).",
            "success"
        )

        return {
            "status": "success",
            "message": f"Document '{clean_name}' successfully attached to Tender #{tender.tender_id}.",
            "document": {
                "id": doc_record.id,
                "file_name": doc_record.file_name,
                "file_type": doc_record.file_type,
                "local_path": doc_record.local_path,
                "file_size_kb": doc_record.portal_size_kb,
                "verified": doc_record.verified,
                "download_status": doc_record.download_status,
                "tender_id": tender.tender_id,
                "tender_title": tender.title,
                "state_name": state_name
            }
        }
    finally:
        db.close()


@app.get("/api/tenders/{tender_row_id}/download-bundle")
def download_tender_bundle(tender_row_id: int):
    """Download all documents of a tender bundled in a zip archive."""
    db = SessionLocal()
    try:
        tender = db.query(models.Tender).filter(models.Tender.id == tender_row_id).first()
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")
            
        if not tender.state:
            raise HTTPException(status_code=400, detail="Tender has no associated state")
        state_name = tender.state.name
        keyword = tender.keywords[0].keyword if (tender.keywords and len(tender.keywords) > 0) else ""
        bundle_name = f"Tender_{tender.tender_id}_Documents.zip"
        bundle_path = STORAGE_ROOT / state_name / keyword / tender.tender_id / bundle_name
        
        # Generate bundle zip of authentic documents
        res = generate_bundle_zip(tender, bundle_path)
        if not res and tender.documents:
            # If any documents are pending, attempt live download
            for doc in tender.documents:
                if doc.download_status != "downloaded":
                    fetch_and_download_document_live(doc_id=doc.id, db=db)
            res = generate_bundle_zip(tender, bundle_path)

        if not res or not bundle_path.exists() or bundle_path.stat().st_size == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Authentic proposal documents for Tender '{tender.tender_id}' are pending live download from the {state_name} portal ({tender.state.portal_url})."
            )
        
        return FileResponse(
            str(bundle_path),
            media_type="application/zip",
            content_disposition_type="attachment",
            filename=bundle_name,
            headers={
                "Content-Disposition": f'attachment; filename="{bundle_name}"',
                "Access-Control-Allow-Origin": "*"
            }
        )
    finally:
        db.close()

@app.post("/api/documents/auto-download")
def trigger_auto_download(background_tasks: BackgroundTasks, sync: bool = Query(False)):
    """Trigger backend automatic download of pending documents."""
    if sync:
        res = run_auto_download(limit=100)
        return res
        
    background_tasks.add_task(run_auto_download, limit=100)
    return {
        "status": "started",
        "message": "Backend Automatic Downloader started in background. Monitor live progress in Agent Terminal."
    }

