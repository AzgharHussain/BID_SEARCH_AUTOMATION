import os
import io
import time
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

from PIL import Image
from app.db.database import SessionLocal
from app.models import models
from app.services.document_service import STORAGE_ROOT, log_scraper_event


def compress_single_pdf(file_path: Path, max_dim: int = 1800, quality: int = 70) -> Dict[str, Any]:
    """
    Compress a single PDF file:
    1. Recompresses and downsamples embedded raster images if oversized.
    2. Compresses content streams, fonts, and removes unused duplicate objects (garbage=4, deflate=True).
    3. Replaces the file if the new size is smaller.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file() or path.suffix.lower() != '.pdf':
        return {"success": False, "error": f"File '{path}' does not exist or is not a PDF"}

    orig_size = path.stat().st_size
    tmp_out = path.parent / f"_comp_{int(time.time()*1000)}_{path.name}"

    try:
        doc = pymupdf.open(str(path))
        
        # Optimize embedded images if the file is larger than 400 KB
        if orig_size > 400 * 1024:
            for page in doc:
                try:
                    for img_info in page.get_images():
                        xref = img_info[0]
                        try:
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image.get("image")
                            if not image_bytes or len(image_bytes) < 100 * 1024:
                                continue
                            
                            img = Image.open(io.BytesIO(image_bytes))
                            if img.width > max_dim or img.height > max_dim:
                                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                                
                            out_buf = io.BytesIO()
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            img.save(out_buf, format='JPEG', quality=quality, optimize=True)
                            compressed_data = out_buf.getvalue()
                            
                            if len(compressed_data) < len(image_bytes):
                                page.replace_image(xref, stream=compressed_data)
                        except Exception:
                            continue
                except Exception:
                    continue

        # Save with maximal compression and object compaction
        doc.save(
            str(tmp_out), 
            garbage=4, 
            deflate=True, 
            clean=True, 
            deflate_images=True, 
            deflate_fonts=True
        )
        doc.close()

        new_size = tmp_out.stat().st_size
        
        if new_size < orig_size:
            # Overwrite original with compressed version
            tmp_out.replace(path)
            saved_bytes = orig_size - new_size
            saved_pct = round((saved_bytes / orig_size) * 100, 1)
            return {
                "success": True,
                "compressed": True,
                "original_size_kb": round(orig_size / 1024, 1),
                "compressed_size_kb": round(new_size / 1024, 1),
                "saved_percent": saved_pct,
                "file_name": path.name
            }
        else:
            # Discard temporary file if no space saved
            if tmp_out.exists():
                tmp_out.unlink()
            return {
                "success": True,
                "compressed": False,
                "original_size_kb": round(orig_size / 1024, 1),
                "compressed_size_kb": round(orig_size / 1024, 1),
                "saved_percent": 0.0,
                "file_name": path.name
            }

    except Exception as e:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except Exception:
                pass
        return {"success": False, "error": str(e), "file_name": path.name}


def compress_all_large_pdfs(threshold_mb: float = 1.0) -> Dict[str, Any]:
    """
    Scan all PDF files in storage exceeding threshold_mb and compress them automatically.
    Updates the database with the compressed size and logs to scraper.log.
    """
    threshold_bytes = int(threshold_mb * 1024 * 1024)
    db = SessionLocal()
    total_scanned = 0
    compressed_count = 0
    total_saved_bytes = 0

    log_scraper_event(f"[PDF COMPRESSION] 🗜️ Scanning for large PDFs (>= {threshold_mb} MB) across all states...", "info")

    try:
        all_docs = db.query(models.Document).all()
        for doc in all_docs:
            if not doc.local_path:
                continue
            p = Path(doc.local_path)
            if p.suffix.lower() == '.pdf' and p.exists():
                sz = p.stat().st_size
                if sz >= threshold_bytes:
                    total_scanned += 1
                    res = compress_single_pdf(p)
                    if res.get("compressed"):
                        compressed_count += 1
                        orig_kb = res.get("original_size_kb", 0)
                        comp_kb = res.get("compressed_size_kb", 0)
                        saved_pct = res.get("saved_percent", 0)
                        diff = int((orig_kb - comp_kb) * 1024)
                        total_saved_bytes += diff
                        doc.portal_size_kb = comp_kb
                        db.commit()
                        log_scraper_event(
                            f"[PDF COMPRESSED] 🗜️ '{p.name}': {orig_kb} KB ➔ {comp_kb} KB ({saved_pct}% saved)", 
                            "success"
                        )

        saved_mb = round(total_saved_bytes / (1024 * 1024), 2)
        summary = f"Scanned {total_scanned} large PDFs: Compressed {compressed_count} files, saving {saved_mb} MB total."
        log_scraper_event(f"[PDF COMPRESSION] ✅ {summary}", "success")
        return {
            "status": "success",
            "threshold_mb": threshold_mb,
            "total_scanned": total_scanned,
            "compressed_count": compressed_count,
            "saved_mb": saved_mb,
            "message": summary
        }
    finally:
        db.close()
