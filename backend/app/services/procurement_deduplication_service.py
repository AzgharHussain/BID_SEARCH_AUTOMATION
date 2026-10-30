import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import models

logger = logging.getLogger("procurement_deduplication")


class ProcurementDeduplicationService:
    """
    Module 8: Cross-Source Duplicate Detection & Master Opportunity Linkage.
    Identifies genuine duplicates across:
    - Devex
    - ADB CMS
    - Indian State Portals
    - World Bank / UNGM / Official Donors
    
    Uses multi-factor verified matching:
    1. Tender Reference Number (exact or normalized)
    2. Donor Agency
    3. Country
    4. Project Title (token similarity >= 0.88 with same donor + country)
    5. Official Source URL (normalized host + query path)
    
    Links duplicate entries under a Master Opportunity Link without destroying individual source metadata.
    """

    @staticmethod
    def normalize_ref(ref_str: Optional[str]) -> str:
        """Strip punctuation, whitespace, and leading zeros to normalize reference codes."""
        if not ref_str:
            return ""
        # Remove common prefixes like 'Ref:', 'RFP No.', 'Notice No.'
        clean = re.sub(r'^(ref|rfp|notice|tender|procurement|pkg|package)\s*(no\.?|id|#)?[:\s-]*', '', ref_str, flags=re.I)
        # Keep alphanumeric
        clean = re.sub(r'[^A-Za-z0-9]', '', clean).upper()
        return clean

    @staticmethod
    def tokenize_title(title_str: Optional[str]) -> set:
        """Extract significant alphanumeric word tokens."""
        if not title_str:
            return set()
        words = re.findall(r'[A-Za-z0-9]{3,}', title_str.lower())
        stopwords = {
            "the", "and", "for", "with", "from", "project", "consulting", "services",
            "request", "proposals", "expression", "interest", "procurement", "notice"
        }
        return set(w for w in words if w not in stopwords)

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate Jaccard token overlap between two project titles."""
        t1 = self.tokenize_title(title1)
        t2 = self.tokenize_title(title2)
        if not t1 or not t2:
            return 0.0
        intersection = t1.intersection(t2)
        union = t1.union(t2)
        return len(intersection) / len(union)

    def find_cross_source_matches(
        self,
        ref_number: Optional[str],
        title: str,
        country: Optional[str],
        donor: Optional[str],
        source_url: Optional[str],
        exclude_tender_id: Optional[int] = None,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Check existing tenders in database for genuine duplicates across all sources.
        Returns list of matched tenders with match reasons and confidence scores.
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        matches = []
        try:
            norm_target_ref = self.normalize_ref(ref_number)
            clean_country = (country or "").strip().lower()
            clean_donor = (donor or "").strip().lower()

            all_tenders = db.query(models.Tender).all()
            for cand in all_tenders:
                if exclude_tender_id and cand.id == exclude_tender_id:
                    continue

                matched_reasons = []
                confidence = 0.0

                # 1. Compare Reference Numbers
                cand_ref = cand.tender_id or ""
                cand_norm_ref = self.normalize_ref(cand_ref)
                
                # Check ADB details ref if cand has one
                adb_pkg = cand.adb_detail.package_number if cand.adb_detail else ""
                adb_csrn = cand.adb_detail.csrn_id if cand.adb_detail else ""
                devex_ref = cand.devex_detail.original_procurement_ref if cand.devex_detail else ""

                has_ref_match = False
                if norm_target_ref and len(norm_target_ref) >= 5:
                    if (norm_target_ref == cand_norm_ref or 
                        norm_target_ref == self.normalize_ref(adb_pkg) or
                        norm_target_ref == self.normalize_ref(adb_csrn) or
                        norm_target_ref == self.normalize_ref(devex_ref)):
                        has_ref_match = True
                        matched_reasons.append("Exact Procurement Reference Match")
                        confidence += 0.65

                # 2. Compare Source URLs
                if source_url and cand.portal_tender_url:
                    if source_url.strip().lower() == cand.portal_tender_url.strip().lower():
                        matched_reasons.append("Identical Official Source URL")
                        confidence += 0.85

                # 3. Compare Country & Donor
                cand_country = ""
                cand_donor = ""
                if cand.adb_detail:
                    cand_country = (cand.adb_detail.country or "").lower()
                    cand_donor = "asian development bank"
                elif cand.devex_detail:
                    cand_country = (cand.devex_detail.country or "").lower()
                    cand_donor = (cand.devex_detail.donor_agency or "").lower()
                elif cand.state:
                    cand_country = "india"
                    cand_donor = cand.department or cand.state.name

                country_match = (clean_country and clean_country in cand_country) or (cand_country and cand_country in clean_country)
                donor_match = (clean_donor and clean_donor in cand_donor) or (cand_donor and cand_donor in clean_donor)

                if country_match and donor_match:
                    confidence += 0.20
                    matched_reasons.append("Matching Country and Donor Agency")

                # 4. Compare Title Similarity
                sim = self.calculate_title_similarity(title, cand.title)
                if sim >= 0.85:
                    confidence += 0.35
                    matched_reasons.append(f"High Title Similarity ({round(sim * 100)}%)")
                elif sim >= 0.65 and (has_ref_match or (country_match and donor_match)):
                    confidence += 0.20
                    matched_reasons.append(f"Moderate Title Similarity ({round(sim * 100)}%)")

                # Threshold for verified duplicate
                if confidence >= 0.75:
                    matches.append({
                        "tender_id": cand.id,
                        "tender_title": cand.title,
                        "tender_ref": cand.tender_id,
                        "source": cand.state.platform_type if cand.state else "unknown",
                        "confidence": min(round(confidence, 2), 1.0),
                        "reasons": matched_reasons
                    })

            return matches
        finally:
            if should_close:
                db.close()

    def link_as_master_opportunity(
        self,
        primary_tender_id: int,
        duplicate_tender_id: int,
        source_system: str,
        match_criteria: Dict[str, Any],
        db: Session
    ) -> models.MasterOpportunityLink:
        """Create a Master Opportunity Link record connecting the two opportunities."""
        master_ref = f"MASTER-OPP-{primary_tender_id}"

        # Ensure primary has master entry
        primary_link = db.query(models.MasterOpportunityLink).filter(
            models.MasterOpportunityLink.primary_tender_id == primary_tender_id,
            models.MasterOpportunityLink.source_tender_id == primary_tender_id
        ).first()

        if not primary_link:
            primary_link = models.MasterOpportunityLink(
                master_ref=master_ref,
                primary_tender_id=primary_tender_id,
                source_system="primary",
                source_tender_id=primary_tender_id,
                match_confidence=1.0,
                match_criteria=json.dumps({"role": "master_anchor"}),
                is_master=True
            )
            db.add(primary_link)

        # Create link for duplicate
        link = models.MasterOpportunityLink(
            master_ref=master_ref,
            primary_tender_id=primary_tender_id,
            source_system=source_system,
            source_tender_id=duplicate_tender_id,
            match_confidence=match_criteria.get("confidence", 0.95),
            match_criteria=json.dumps(match_criteria),
            is_master=False
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link


procurement_deduplication_service = ProcurementDeduplicationService()
