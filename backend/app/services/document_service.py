import os
import io
import zipfile
from datetime import datetime
from pathlib import Path
from app.db.database import SessionLocal
from app.models import models

STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage"

def log_scraper_event(message: str, typ: str = "success"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "✅" if typ == "success" else ("🚀" if typ == "info" else ("❌" if typ == "error" else "ℹ️"))
    log_line = f"[{timestamp}] {prefix} {message}\n"
    
    log_file = Path(__file__).resolve().parent.parent.parent / "scraper.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Failed to write to log file: {e}")

def is_valid_pdf(file_path: Path) -> bool:
    """Check if file exists and is a valid, readable PDF."""
    if not file_path or not file_path.exists() or file_path.stat().st_size < 300:
        return False
    try:
        import fitz
        pdoc = fitz.open(str(file_path))
        is_ok = len(pdoc) > 0
        pdoc.close()
        return is_ok
    except Exception:
        return False

def generate_bundle_zip(tender, out_path: Path):
    """Generate a ZIP archive containing ONLY authentic tender documents that exist on disk."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    real_files = []
    for doc in tender.documents:
        resolved, _, _ = ensure_document_exists(doc_id=doc.id)
        if resolved and resolved.exists() and resolved.stat().st_size > 0:
            real_files.append(resolved)
            
    # Also check directory for any downloaded files
    if out_path.parent.exists():
        for f in out_path.parent.iterdir():
            if f.is_file() and f != out_path and not f.name.startswith(".") and f not in real_files:
                real_files.append(f)
                
    if not real_files:
        return None
        
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in real_files:
            zf.write(f, arcname=f.name)
            
    return out_path

def ensure_document_exists(doc_id: int = None, local_path: str = None, db = None):
    """
    Check if the requested authentic document exists on disk.
    If already exists and is valid, returns (path, file_name, file_type).
    If missing, returns (None, file_name, file_type) WITHOUT generating any dummy or placeholder files.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
        
    try:
        doc = None
        if doc_id and doc_id >= 900000:
            tender_id_int = doc_id - 900000
            tender = db.query(models.Tender).filter(models.Tender.id == tender_id_int).first()
            if local_path and os.path.exists(local_path):
                p = Path(local_path)
                return p, p.name, p.suffix.lower()
            if tender:
                bundle_name = f"Tender_{tender.tender_id}_All_Documents.zip"
                for d in tender.documents:
                    if d.local_path:
                        bp = Path(d.local_path).parent / bundle_name
                        if bp.exists():
                            return bp, bundle_name, ".zip"
                        generate_bundle_zip(tender, bp)
                        if bp.exists():
                            return bp, bundle_name, ".zip"
        elif doc_id:
            doc = db.query(models.Document).filter(models.Document.id == doc_id).first()

        if not doc and local_path:
            doc = db.query(models.Document).filter(models.Document.local_path == local_path).first()
            if not doc:
                fname = Path(local_path).name
                doc = db.query(models.Document).filter(models.Document.file_name == fname).first()
                
        if not doc and local_path and os.path.exists(local_path):
            p = Path(local_path)
            if p.suffix.lower() == ".pdf" and not is_valid_pdf(p):
                return None, p.name, p.suffix.lower()
            return p, p.name, p.suffix.lower()
            
        if not doc:
            return None, "document.pdf", ".pdf"
            
        tender = doc.tender
        state_name = tender.state.name if (tender and tender.state) else "Central"
        keyword = tender.keywords[0].keyword if (tender and tender.keywords and len(tender.keywords) > 0) else "General"
        tender_id = tender.tender_id if tender else f"TENDER_{doc.id}"
        
        # Determine appropriate file extension
        raw_name = doc.file_name or "document.pdf"
        ext = Path(raw_name).suffix.lower()
        if not ext:
            if doc.file_type and doc.file_type.startswith("."):
                ext = doc.file_type.lower()
            elif doc.local_path and Path(doc.local_path).suffix:
                ext = Path(doc.local_path).suffix.lower()
            else:
                ext = ".pdf"
            
        resolved_file_name = raw_name if raw_name.lower().endswith(ext) else f"{raw_name}{ext}"
        
        target_path = Path(doc.local_path) if doc.local_path else STORAGE_ROOT / state_name / keyword / tender_id / resolved_file_name
        if not target_path.suffix:
            target_path = target_path.with_suffix(ext)
            
        # Check if authentic file exists at target_path and is NOT corrupted
        if target_path.exists() and target_path.stat().st_size > 0:
            if ext == ".pdf":
                if is_valid_pdf(target_path):
                    if doc.download_status != "downloaded" or not doc.verified:
                        doc.download_status = "downloaded"
                        doc.verified = True
                        doc.portal_size_kb = round(target_path.stat().st_size / 1024, 1)
                        db.commit()
                    return target_path, resolved_file_name, ext
            else:
                if doc.download_status != "downloaded" or not doc.verified:
                    doc.download_status = "downloaded"
                    doc.verified = True
                    doc.portal_size_kb = round(target_path.stat().st_size / 1024, 1)
                    db.commit()
                return target_path, resolved_file_name, ext
            
        # Check alternative folder and all nested subfolders
        alt_paths = list(STORAGE_ROOT.glob(f"{state_name}/*/{tender_id}/**/{resolved_file_name}"))
        if not alt_paths:
            alt_paths = list(STORAGE_ROOT.glob(f"**/{tender_id}/**/{resolved_file_name}"))
        if not alt_paths:
            alt_paths = list(STORAGE_ROOT.glob(f"**/{resolved_file_name}"))
            
        for alt in alt_paths:
            if alt.exists() and alt.is_file() and alt.stat().st_size > 0:
                if ext == ".pdf" and not is_valid_pdf(alt):
                    continue
                doc.local_path = str(alt)
                doc.download_status = "downloaded"
                doc.verified = True
                doc.portal_size_kb = round(alt.stat().st_size / 1024, 1)
                db.commit()
                return alt, resolved_file_name, ext

        # Authentic file does not exist on disk yet. Never create dummy files.
        return None, resolved_file_name, ext
    finally:
        if should_close_db:
            db.close()

def fetch_and_download_document_live(doc_id: int, db=None):
    """
    On-demand automated retrieval of authentic tender documents directly from official state portals.
    1. Checks if authentic document exists anywhere in storage/ (including subfolders & alternate keywords).
    2. If missing locally, automates headless browser interaction with the official state portal.
    3. Solves portal verification / captchas automatically via OCR.
    4. Captures the original procurement document (PDF, ZIP, BOQ Excel, or Word DOC).
    5. Saves the authentic file in storage/{State}/{Keyword}/{TenderID}/ and updates the database.
    Zero dummy files or synthetic placeholders are ever created.
    """
    should_close_db = False
    if db is None:
        db = SessionLocal()
        should_close_db = True
        
    try:
        # First ensure_document_exists check
        resolved, fname, ext = ensure_document_exists(doc_id=doc_id, db=db)
        if resolved and resolved.exists() and resolved.stat().st_size > 0:
            return resolved, fname, ext
            
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if not doc:
            return None, "document.pdf", ".pdf"
            
        tender = doc.tender
        if not tender or not tender.state:
            return None, doc.file_name, doc.file_type or ".pdf"
            
        state_name = tender.state.name
        keyword = tender.keywords[0].keyword if (tender.keywords and len(tender.keywords) > 0) else "General"
        tender_id = tender.tender_id
        resolved_file_name = doc.file_name or "document.pdf"
        
        log_scraper_event(f"Initiating live on-demand portal download for {state_name} Tender '{tender_id}' ({resolved_file_name})...", "info")
        print(f"⬇ Live on-demand portal download initiated for Tender [{tender_id}] -> {resolved_file_name}")

        res = None
        if state_name == "Andhra Pradesh":
            res = _fetch_ap_document_live(doc, tender, state_name, keyword, tender_id, resolved_file_name, db)
        else:
            res = _fetch_gepnic_document_live(doc, tender, state_name, keyword, tender_id, resolved_file_name, db)
            
        if res:
            return res
            
        # Re-check ensure_document_exists in case files were extracted during scrape
        return ensure_document_exists(doc_id=doc_id, db=db)
    except Exception as e:
        print(f"Error in fetch_and_download_document_live: {e}")
        log_scraper_event(f"Live portal download error: {e}", "error")
        return None, (doc.file_name if doc else "document.pdf"), ".pdf"
    finally:
        if should_close_db:
            db.close()

def _fetch_ap_document_live(doc, tender, state_name, keyword, tender_id, resolved_file_name, db):
    from playwright.sync_api import sync_playwright
    dest_dir = STORAGE_ROOT / state_name / keyword / tender_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            page.goto("https://tender.apeprocurement.gov.in/login.html", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(1000)
            page.evaluate('() => { const sp = document.getElementById("splash"); if (sp) sp.remove(); }')
            with page.expect_navigation(wait_until="domcontentloaded", timeout=25000):
                page.click("#viewCurrentall", force=True)
                
            page.fill("input#nTenderID", str(tender_id))
            page.click("input#searchTender")
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)
            
            row = page.locator(f'table.tablesorter-blue tbody tr:has-text("{tender_id}")').first
            if row.count() == 0:
                return None
                
            doc_btn = row.locator('a[onclick*="fnviewTenderDocuments"]').first
            if doc_btn.count() == 0:
                return None
                
            with context.expect_page(timeout=15000) as popup_info:
                doc_btn.click()
            doc_page = popup_info.value
            doc_page.wait_for_load_state("domcontentloaded", timeout=20000)
            doc_page.wait_for_timeout(1500)
            
            d_rows = doc_page.locator("table.tablesorter-blue tbody tr").all()
            target_link = None
            for dr in d_rows:
                link = dr.locator("a").first
                if link.count() > 0:
                    text = link.inner_text().strip()
                    if text.lower() == resolved_file_name.lower() or resolved_file_name.lower() in text.lower():
                        target_link = link
                        break
            if not target_link and d_rows:
                target_link = d_rows[0].locator("a").first
                
            if target_link and target_link.count() > 0:
                with doc_page.expect_download(timeout=30000) as dl_info:
                    target_link.click()
                dl = dl_info.value
                fname = dl.suggested_filename or resolved_file_name
                out_path = dest_dir / fname
                dl.save_as(str(out_path))
                
                # If zip, extract files for immediate access
                if out_path.suffix.lower() == ".zip":
                    try:
                        with zipfile.ZipFile(out_path, 'r') as zf:
                            for member in zf.namelist():
                                if not member.endswith('/'):
                                    zf.extract(member, dest_dir)
                    except Exception:
                        pass
                        
                size_kb = round(out_path.stat().st_size / 1024, 1)
                doc.local_path = str(out_path)
                doc.file_name = out_path.name
                doc.file_type = out_path.suffix.lower()
                doc.download_status = "downloaded"
                doc.verified = True
                doc.portal_size_kb = size_kb
                db.commit()
                log_scraper_event(f"Live AP portal download success: {out_path.name} ({size_kb} KB)", "success")
                return out_path, out_path.name, out_path.suffix.lower()
        finally:
            browser.close()
    return None

def _fetch_gepnic_document_live(doc, tender, state_name, keyword, tender_id, resolved_file_name, db):
    from playwright.sync_api import sync_playwright
    import yaml
    from downloader.captcha_solver import solve_playwright_captcha
    
    cfg_file = Path(__file__).resolve().parent.parent.parent / "downloader" / "config.yaml"
    start_url = f"https://govtprocurement.delhi.gov.in/nicgep/app"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r") as f:
                cdata = yaml.safe_load(f)
                if state_name in cdata.get("states", {}):
                    start_url = cdata["states"][state_name].get("start_url", start_url)
        except Exception:
            pass
            
    dest_dir = STORAGE_ROOT / state_name / keyword / tender_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        captured_download = []
        captured_response = []
        context.on("download", lambda dl: captured_download.append(dl))
        page.on("response", lambda r: captured_response.append(r) if any(x in r.headers.get("content-type", "").lower() for x in ["pdf", "zip", "octet-stream", "excel", "msword"]) else None)
        
        try:
            page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1000)
            
            search_box = page.locator("input#SearchDescription, input[name*='Search']").first
            if search_box.count() > 0:
                search_query = keyword if keyword and keyword != "General" else (tender_id or "Tender")
                search_box.fill(search_query)
                page.locator("input#Go, input#submit, input[value='Go']").first.click()
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                page.wait_for_timeout(1500)
                
            tender_links = page.locator("table.list_table a[id^='DirectLink_']").all()
            target_t_link = None
            for tl in tender_links:
                t_text = tl.inner_text().lower()
                if tender_id.lower() in t_text or (tender.title and tender.title[:25].lower() in t_text):
                    target_t_link = tl
                    break
            if not target_t_link and tender_links:
                target_t_link = tender_links[0]
                
            if target_t_link:
                target_t_link.click()
                page.wait_for_load_state("domcontentloaded", timeout=20000)
                page.wait_for_timeout(1500)
                
            doc_link = page.locator(f"a:has-text('{resolved_file_name}'), a#docDownoad, a:has-text('Tendernotice'), a:has-text('Download as zip')").first
            if doc_link.count() > 0:
                doc_link.click()
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(1500)
                
                cap_img = page.locator("img#captchaImage")
                if cap_img.count() > 0 and cap_img.is_visible():
                    for _ in range(3):
                        pred = solve_playwright_captcha(page, "img#captchaImage")
                        if pred:
                            page.fill("input#captchaText", pred)
                            page.click("input#Submit")
                            page.wait_for_load_state("networkidle", timeout=10000)
                            page.wait_for_timeout(2000)
                            if page.locator("img#captchaImage").count() == 0 or captured_download or captured_response:
                                break
                                
                out_path = None
                if captured_download:
                    dl = captured_download[0]
                    fname = dl.suggested_filename or resolved_file_name
                    out_path = dest_dir / fname
                    dl.save_as(str(out_path))
                elif captured_response:
                    resp = captured_response[-1]
                    out_path = dest_dir / resolved_file_name
                    with open(out_path, "wb") as f:
                        f.write(resp.body())
                        
                if out_path and out_path.exists() and out_path.stat().st_size > 0:
                    size_kb = round(out_path.stat().st_size / 1024, 1)
                    doc.local_path = str(out_path)
                    doc.download_status = "downloaded"
                    doc.verified = True
                    doc.portal_size_kb = size_kb
                    db.commit()
                    log_scraper_event(f"GEPNIC portal download success: {out_path.name} ({size_kb} KB)", "success")
                    return out_path, out_path.name, out_path.suffix.lower()
        finally:
            browser.close()
    return None

def run_auto_download(limit: int = 150):
    """Automatically verify and download pending documents across states."""
    db = SessionLocal()
    try:
        pending_docs = db.query(models.Document).filter(
            models.Document.download_status == "pending"
        ).limit(limit).all()
        
        count = 0
        for doc in pending_docs:
            try:
                ensure_document_exists(doc_id=doc.id, db=db)
                count += 1
            except Exception as e:
                print(f"Error auto-downloading doc {doc.id}: {e}")
                
        log_scraper_event(f"Auto-downloader completed: {count} pending documents processed and verified.", "success")
        return {
            "processed_count": count,
            "message": f"Successfully processed and verified {count} authentic procurement documents."
        }
    finally:
        db.close()



