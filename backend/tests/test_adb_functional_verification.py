import os
import json
import hashlib
import zipfile
import unittest
from pathlib import Path
from datetime import datetime

import pymupdf as fitz
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models import models
from app.services.adb_cms_connector import adb_connector, calculate_file_sha256

class TestAdbCmsFunctionalVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_three_distinct_countries_present(self):
        """Verify at least 3 real opportunities from different countries exist."""
        tenders = self.db.query(models.Tender).filter(
            models.Tender.state.has(platform_type="adb_cms")
        ).all()
        self.assertGreaterEqual(len(tenders), 3, "Must have at least 3 ADB opportunities synced")
        
        countries = [t.adb_detail.country for t in tenders if t.adb_detail and t.adb_detail.country]
        distinct_countries = set(countries)
        print(f"Distinct countries found: {distinct_countries}")
        self.assertGreaterEqual(len(distinct_countries), 3, "Must have opportunities from at least 3 distinct countries")
        self.assertIn("Pakistan", distinct_countries)
        self.assertIn("Cambodia", distinct_countries)
        self.assertIn("China", distinct_countries)

    def test_02_field_by_field_integrity(self):
        """Field-by-field verification of original ADB published data."""
        # 1. Pakistan
        pak = self.db.query(models.Tender).filter(
            models.Tender.adb_detail.has(country="Pakistan")
        ).first()
        self.assertIsNotNone(pak)
        self.assertIn("Pakistan Railways Main Line-1", pak.title)
        self.assertEqual(pak.adb_detail.country, "Pakistan")
        self.assertEqual(pak.adb_detail.executing_agency, "Ministry of Railways")
        self.assertEqual(pak.adb_detail.selection_method, "Quality and Cost-Based Selection (QCBS)")
        self.assertEqual(pak.adb_detail.consultant_source, "International")
        self.assertEqual(pak.adb_detail.budget_amount, 60115232.0)
        self.assertEqual(pak.adb_detail.budget_currency, "USD")
        self.assertEqual(pak.adb_detail.engagement_period_months, 72.0)
        self.assertEqual(pak.adb_detail.eoi_deadline_str, "22-Nov-2026 11:59 PM")
        # IST is Manila - 2h30m -> 21:29:00
        self.assertEqual(pak.last_date.strftime("%Y-%m-%d %H:%M:%S"), "2026-11-22 21:29:00")

        # 2. Cambodia
        cam = self.db.query(models.Tender).filter(
            models.Tender.adb_detail.has(country="Cambodia")
        ).first()
        self.assertIsNotNone(cam)
        self.assertIn("Integrated Water Resources Management", cam.title)
        self.assertEqual(cam.adb_detail.country, "Cambodia")
        self.assertEqual(cam.adb_detail.executing_agency, "Ministry of Water Resources and Meteorology")
        self.assertEqual(cam.adb_detail.selection_method, "Consultants' Qualifications Selection (CQS)")
        self.assertEqual(cam.adb_detail.consultant_source, "National")
        self.assertEqual(cam.adb_detail.budget_amount, 150000.0)
        self.assertEqual(cam.adb_detail.eoi_deadline_str, "21-Nov-2026 11:59 PM")
        self.assertEqual(cam.last_date.strftime("%Y-%m-%d %H:%M:%S"), "2026-11-21 21:29:00")

        # 3. China
        chn = self.db.query(models.Tender).filter(
            models.Tender.adb_detail.has(country="China")
        ).first()
        self.assertIsNotNone(chn)
        self.assertIn("Yellow River Basin", chn.title)
        self.assertEqual(chn.adb_detail.country, "China")
        self.assertIn("Ministry of Agriculture and Rural Affairs", chn.adb_detail.executing_agency)
        self.assertEqual(chn.adb_detail.selection_method, "Quality and Cost-Based Selection (QCBS)")
        self.assertEqual(chn.adb_detail.consultant_source, "National")
        self.assertEqual(chn.adb_detail.budget_amount, 280000.0)
        self.assertEqual(chn.adb_detail.eoi_deadline_str, "19-Nov-2026 11:59 PM")
        self.assertEqual(chn.last_date.strftime("%Y-%m-%d %H:%M:%S"), "2026-11-19 21:29:00")

    def test_03_downloaded_documents_and_checksum_verification(self):
        """Validate every downloaded document on disk: file exists, size > 0, SHA-256 match, and PDF readable."""
        docs = self.db.query(models.Document).filter(
            models.Document.tender.has(models.Tender.state.has(platform_type="adb_cms")),
            models.Document.access_status == "Verified"
        ).all()
        self.assertGreaterEqual(len(docs), 3)

        for doc in docs:
            self.assertTrue(os.path.exists(doc.local_path), f"File {doc.local_path} must exist on disk")
            size = os.path.getsize(doc.local_path)
            self.assertGreater(size, 0, f"File {doc.file_name} must not be zero bytes")
            self.assertEqual(size, doc.file_size_bytes, f"Size mismatch for {doc.file_name}")

            # Recompute SHA-256 hash
            actual_sha = calculate_file_sha256(Path(doc.local_path))
            self.assertEqual(actual_sha, doc.sha256_hash, f"SHA-256 checksum mismatch for {doc.file_name}")

            # Verify PyMuPDF can open and parse pages
            if doc.file_type.lower() == "pdf":
                pdf_doc = fitz.open(doc.local_path)
                page_cnt = pdf_doc.page_count
                self.assertGreater(page_cnt, 0, f"PDF {doc.file_name} must have at least 1 page")
                text = pdf_doc[0].get_text()
                self.assertGreater(len(text), 20, f"PDF {doc.file_name} must have readable text")
                pdf_doc.close()
                print(f"Verified PDF {doc.file_name}: {size} bytes, {page_cnt} pages, SHA256: {actual_sha[:16]}...")

    def test_04_zip_export_and_manifest(self):
        """Verify ZIP packaging, manifest.json schema, and document reconciliation."""
        pak = self.db.query(models.Tender).filter(models.Tender.adb_detail.has(country="Pakistan")).first()
        res = self.client.get(f"/api/adb/opportunities/{pak.id}/download-all-zip")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "application/zip")

        # Inspect ZIP
        zip_bytes = res.content
        self.assertGreater(len(zip_bytes), 10000)
        
        # Test zip integrity
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            namelist = zf.namelist()
            self.assertIn("manifest.json", namelist)
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            self.assertEqual(manifest["manifest_version"], "1.0")
            self.assertEqual(manifest["opportunity"]["country"], "Pakistan")
            self.assertGreaterEqual(len(manifest["documents"]), 1)
            for d in manifest["documents"]:
                self.assertIn("sha256_hash", d)
                self.assertIn("size_bytes", d)
                self.assertEqual(d["access_status"], "Verified")

    def test_05_api_filters_and_search(self):
        """Test API filtering by country, sector, consultant type, and keyword search."""
        # Filter by country
        res_cam = self.client.get("/api/adb/opportunities?country=Cambodia")
        self.assertEqual(res_cam.status_code, 200)
        data_cam = res_cam.json()
        self.assertGreaterEqual(data_cam["total"], 1)
        for it in data_cam["items"]:
            self.assertEqual(it["detail"]["country"], "Cambodia")

        # Filter by sector
        res_rail = self.client.get("/api/adb/opportunities?sector=Railways")
        self.assertEqual(res_rail.status_code, 200)
        data_rail = res_rail.json()
        self.assertGreaterEqual(data_rail["total"], 1)

        # Keyword search
        res_search = self.client.get("/api/adb/opportunities?search=Yellow%20River")
        self.assertEqual(res_search.status_code, 200)
        data_search = res_search.json()
        self.assertGreaterEqual(data_search["total"], 1)
        self.assertIn("Yellow River", data_search["items"][0]["title"])

    def test_06_eoi_tracker_pipeline_update(self):
        """Verify advancing EOI / proposal tracker through its official stages."""
        pak = self.db.query(models.Tender).filter(models.Tender.adb_detail.has(country="Pakistan")).first()
        res = self.client.post(
            f"/api/adb/opportunities/{pak.id}/tracker",
            json={
                "pipeline_stage": "EOI In Preparation",
                "stage_status": "manual_entry",
                "internal_notes": "Technical proposal team assembled with lead partner.",
                "submission_reference": "GISFY-ADB-PAK-2026-001",
                "lead_partner_name": "GISFY PVT LTD"
            }
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["pipeline_stage"], "EOI In Preparation")

        # Verify detail endpoint returns updated tracker and history
        detail_res = self.client.get(f"/api/adb/opportunities/{pak.id}")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.json()
        self.assertEqual(detail_data["tracker"]["pipeline_stage"], "EOI In Preparation")
        self.assertEqual(detail_data["tracker"]["submission_reference"], "GISFY-ADB-PAK-2026-001")
        self.assertGreaterEqual(len(detail_data["tracker"]["history"]), 2)

    def test_07_source_data_differs_from_ai_analysis(self):
        """Verify that source-backed data is strictly distinguished from AI-generated summary fields."""
        pak = self.db.query(models.Tender).filter(models.Tender.adb_detail.has(country="Pakistan")).first()
        res = self.client.get(f"/api/adb/opportunities/{pak.id}")
        data = res.json()

        # Source data must have source_verified = True and official URL
        self.assertTrue(data["detail"]["source_verified"])
        self.assertIn("adb.org", data["detail"]["official_source_url"])

        # AI analysis must be clearly labeled as internal and distinct
        ai = data["ai_analysis"]
        self.assertIn("GISFY Internal AI Assessment", ai["analysis_type"])
        self.assertIn("Not official ADB evaluation", ai["analysis_type"])
        self.assertIsInstance(ai["readiness_score"], float)
        self.assertGreaterEqual(len(ai["key_experts"]), 3)
        self.assertGreaterEqual(len(ai["recommended_partners"]), 1)
    def test_08_proposal_dossier_generation(self):
        """Verify generating authentic ADB EOI Proposal Dossier PDF."""
        pak = self.db.query(models.Tender).filter(models.Tender.adb_detail.has(country="Pakistan")).first()
        res = self.client.get(f"/api/adb/opportunities/{pak.id}/proposal-dossier")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("content-type"), "application/pdf")
        self.assertGreater(len(res.content), 5000)

        # Verify PDF structure using PyMuPDF
        pdf_doc = fitz.open(stream=res.content, filetype="pdf")
        self.assertGreaterEqual(pdf_doc.page_count, 2)
        txt_p1 = pdf_doc[0].get_text()
        self.assertIn("ASIAN DEVELOPMENT BANK", txt_p1)
        self.assertIn("EXPRESSION OF INTEREST", txt_p1)
        self.assertIn("GISFY PVT LTD", txt_p1)
        pdf_doc.close()

    def test_09_keyword_domain_filtering(self):
        """Verify keyword domain filtering reflects genuine opportunities."""
        res_water = self.client.get("/api/adb/opportunities?keyword=Water%20Resources")
        self.assertEqual(res_water.status_code, 200)
        data_water = res_water.json()
        self.assertGreaterEqual(data_water["total"], 1)

        res_climate = self.client.get("/api/adb/opportunities?keyword=Climate%20Change")
        self.assertEqual(res_climate.status_code, 200)
        data_climate = res_climate.json()
        self.assertGreaterEqual(data_climate["total"], 1)


if __name__ == "__main__":
    unittest.main()
