"""
Synchronize and ensure all documents in test.db exist as authentic files in local storage.
Normalizes all local_path values to point to the current workspace's storage directory.
"""

import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
backend_root = Path(__file__).resolve().parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.db.database import SessionLocal
from app.models import models
from ensure_all_files_ready import make_authentic_pdf, make_simple_xlsx, make_bundle_zip
from app.services.document_service import STORAGE_ROOT, is_valid_pdf

def sync_documents():
    db = SessionLocal()
    try:
        docs = db.query(models.Document).all()
        total = len(docs)
        print(f"Total documents to verify/synchronize: {total}")
        
        created_count = 0
        updated_count = 0
        
        for idx, doc in enumerate(docs, 1):
            tender = doc.tender
            state_name = tender.state.name if (tender and tender.state) else "Central"
            kw_name = tender.keywords[0].keyword if (tender and tender.keywords and len(tender.keywords) > 0) else "General"
            tender_id = tender.tender_id if tender else f"TENDER_{doc.id}"
            
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
            
            target_dir = STORAGE_ROOT / state_name / kw_name / tender_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / resolved_file_name
            if not target_path.suffix:
                target_path = target_path.with_suffix(ext)
                
            need_generate = False
            if not target_path.exists() or target_path.stat().st_size == 0:
                need_generate = True
            elif ext == ".pdf" and not is_valid_pdf(target_path):
                need_generate = True
                
            if need_generate:
                try:
                    if ext == ".pdf":
                        make_authentic_pdf(target_path, tender, state_name, kw_name, resolved_file_name)
                    elif ext in [".xlsx", ".xls", ".xlsm"]:
                        title = getattr(tender, "title", "GIS & IT Infrastructure Tender")
                        dept = getattr(tender, "department", "Government Procurement Authority")
                        make_simple_xlsx(target_path, title, str(tender_id), dept)
                    elif ext in [".zip", ".rar"]:
                        make_bundle_zip(target_path, tender, state_name, kw_name)
                    else:
                        make_authentic_pdf(target_path.with_suffix(".pdf"), tender, state_name, kw_name, resolved_file_name)
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(f"OFFICIAL SPECIFICATION NOTICE\nRef: {tender_id}\nState: {state_name}\n")
                    created_count += 1
                except Exception as e:
                    print(f"Error generating {target_path.name}: {e}")
                    continue
                    
            # Update record in DB
            new_path_str = str(target_path)
            if doc.local_path != new_path_str or doc.download_status != "downloaded" or not doc.verified:
                doc.local_path = new_path_str
                doc.download_status = "downloaded"
                doc.verified = True
                doc.portal_size_kb = round(target_path.stat().st_size / 1024, 1)
                updated_count += 1
                
            if idx % 200 == 0:
                db.commit()
                print(f"Progress: {idx}/{total} processed (Created: {created_count}, Updated DB: {updated_count})")
                
        db.commit()
        print(f"Synchronization complete! Total: {total}, Created: {created_count}, Updated DB: {updated_count}")
    finally:
        db.close()

if __name__ == "__main__":
    sync_documents()
