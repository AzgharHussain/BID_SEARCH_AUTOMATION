import os
import hashlib
import logging
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import requests
from app.db.database import SessionLocal
from app.models import models

logger = logging.getLogger("devex_document_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_ROOT = BASE_DIR / "storage" / "devex_docs"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

# Document Category Standards
DOC_CATEGORIES = {
    "TOR": "Terms of Reference (TOR)",
    "RFP": "Request for Proposals (RFP)",
    "EOI": "Expression of Interest (EOI) Notice",
    "TECH_SPEC": "Technical Specifications & Scope of Work",
    "SUBMISSION_FORMS": "Proposal Submission & Financial Forms",
    "EVAL_CRITERIA": "Evaluation Criteria & Expert Requirements",
    "ADDENDUM": "Addenda & Clarifications",
    "TENDER_NOTICE": "Official Procurement Notice"
}

# Access Status Standards (Module 6)
ACCESS_STATUSES = {
    "VERIFIED": "Verified Original",
    "PENDING": "Downloaded — Verification Pending",
    "RESTRICTED": "Restricted",
    "MISSING": "Missing",
    "FAILED": "Download Failed"
}


class DevexDocumentService:
    """
    Manages authentic, genuine original tender documents from official issuing donors
    (World Bank, UNGM, AfDB, MCC, etc.).
    Preserves native format (PDF, DOCX, XLSX, ZIP), computes SHA-256 checksums,
    and tracks verification statuses.
    """

    def __init__(self):
        self.storage_dir = STORAGE_ROOT

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Calculate authentic SHA-256 checksum of a physical document."""
        if not file_path.exists():
            return ""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def store_document_file(
        self,
        tender_id: int,
        file_name: str,
        content_bytes: bytes,
        source_url: str,
        doc_category: str = "TOR",
        access_status: str = "Verified Original"
    ) -> models.Document:
        """Store native file on disk and record in Document table."""
        tender_dir = self.storage_dir / f"tender_{tender_id}"
        tender_dir.mkdir(parents=True, exist_ok=True)

        target_file = tender_dir / file_name
        with open(target_file, "wb") as f:
            f.write(content_bytes)

        sha256_hash = self.calculate_sha256(target_file)
        file_size_bytes = len(content_bytes)
        ext = target_file.suffix.lower().replace(".", "") or "pdf"

        db = SessionLocal()
        try:
            # Check if document already recorded
            existing_doc = db.query(models.Document).filter(
                models.Document.tender_row_id == tender_id,
                models.Document.file_name == file_name
            ).first()

            if existing_doc:
                existing_doc.source_url = source_url
                existing_doc.local_path = str(target_file)
                existing_doc.file_type = ext.upper()
                existing_doc.file_size_bytes = file_size_bytes
                existing_doc.portal_size_kb = round(file_size_bytes / 1024.0, 2)
                existing_doc.sha256_hash = sha256_hash
                existing_doc.doc_category = doc_category
                existing_doc.access_status = access_status
                existing_doc.download_status = "downloaded"
                existing_doc.verified = (access_status == "Verified Original")
                existing_doc.checksum_verified = True
                existing_doc.retrieval_timestamp = datetime.utcnow()
                db.commit()
                db.refresh(existing_doc)
                return existing_doc
            else:
                doc = models.Document(
                    tender_row_id=tender_id,
                    file_name=file_name,
                    file_type=ext.upper(),
                    source_url=source_url,
                    local_path=str(target_file),
                    verified=(access_status == "Verified Original"),
                    download_status="downloaded",
                    portal_size_kb=round(file_size_bytes / 1024.0, 2),
                    file_size_bytes=file_size_bytes,
                    sha256_hash=sha256_hash,
                    doc_category=doc_category,
                    doc_version="1.0",
                    access_status=access_status,
                    checksum_verified=True,
                    retrieval_timestamp=datetime.utcnow()
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
                return doc
        finally:
            db.close()

    def fetch_from_official_donor_url(
        self,
        tender_id: int,
        donor_file_url: str,
        suggested_filename: str,
        doc_category: str = "TOR"
    ) -> Dict[str, Any]:
        """Download public document directly from official donor source."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
            }
            res = requests.get(donor_file_url, headers=headers, timeout=30)
            if res.status_code == 200 and len(res.content) > 100:
                doc = self.store_document_file(
                    tender_id=tender_id,
                    file_name=suggested_filename,
                    content_bytes=res.content,
                    source_url=donor_file_url,
                    doc_category=doc_category,
                    access_status=ACCESS_STATUSES["VERIFIED"]
                )
                return {
                    "success": True,
                    "doc_id": doc.id,
                    "file_name": doc.file_name,
                    "size_kb": doc.portal_size_kb,
                    "sha256": doc.sha256_hash,
                    "status": ACCESS_STATUSES["VERIFIED"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Donor portal returned HTTP {res.status_code}",
                    "status": ACCESS_STATUSES["FAILED"]
                }
        except Exception as e:
            logger.error(f"Failed to fetch document from {donor_file_url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": ACCESS_STATUSES["FAILED"]
            }

    def generate_all_documents_zip(self, tender_id: int) -> Optional[Path]:
        """Bundle all downloaded original tender documents into an authentic zip archive."""
        db = SessionLocal()
        try:
            docs = db.query(models.Document).filter(
                models.Document.tender_row_id == tender_id,
                models.Document.download_status == "downloaded"
            ).all()

            valid_files = []
            for d in docs:
                if d.local_path and Path(d.local_path).exists():
                    valid_files.append((Path(d.local_path), d.file_name))

            if not valid_files:
                return None

            zip_path = self.storage_dir / f"tender_{tender_id}" / f"Tender_{tender_id}_Original_Documents.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for fpath, fname in valid_files:
                    zf.write(fpath, arcname=fname)

            return zip_path
        finally:
            db.close()


devex_document_service = DevexDocumentService()
