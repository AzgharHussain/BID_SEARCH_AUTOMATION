import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import models
from app.services.collaboration_email_service import (
    generate_project_technical_scope,
    build_collaboration_email_text,
    build_collaboration_email_html,
    get_gisfy_logo_src
)

logger = logging.getLogger("devex_partner_service")


class DevexPartnerService:
    """
    Module 11: JV & Consortium Partner Recommendation Engine for Devex Opportunities.
    Recommends verified firms based on:
    - Target country presence (local in-country partner)
    - Domain and technical specialization (GIS, Water, Transport, Climate, Agriculture)
    - Multilateral donor project track record (World Bank, UN, AfDB, etc.)
    - Generates drafts using GISFY standard template (strictly without auto-sending).
    """

    def recommend_partners_for_opportunity(
        self,
        tender_id: int,
        limit: int = 5,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
            if not tender or not tender.devex_detail:
                return []

            dev = tender.devex_detail
            target_country = (dev.country or "").strip().lower()
            target_sector = (dev.project_sector or "").strip().lower()
            combined_scope = f"{tender.title} {dev.scope_of_work or ''} {dev.technical_requirements or ''}".lower()

            all_partners = db.query(models.Partner).all()
            scored_partners = []

            for p in all_partners:
                p_country = (p.state or "").strip().lower()
                p_domain = f"{p.primary_domain or ''} {p.secondary_domains or ''} {p.description or ''}".lower()

                match_score = 50.0  # Base score
                reasons = []

                # Country Match
                if target_country and (target_country in p_country or p_country in target_country):
                    match_score += 30.0
                    reasons.append(f"In-Country Partner: Registered physical presence in {dev.country}")
                elif p.pan_india_presence and target_country in ["india", ""]:
                    match_score += 25.0
                    reasons.append("National Presence: Extensive Pan-India footprint")

                # Technical Domain Match
                if any(w in p_domain and w in combined_scope for w in ["gis", "webgis", "spatial", "mapping"]):
                    match_score += 15.0
                    reasons.append("Technical Synergy: Deep GIS and spatial data infrastructure capabilities")
                if any(w in p_domain and w in combined_scope for w in ["water", "hydrology", "canal", "river"]):
                    match_score += 15.0
                    reasons.append("Domain Synergy: Water resources and hydrological modeling track record")
                if any(w in p_domain and w in combined_scope for w in ["drone", "uav", "lidar", "aerial"]):
                    match_score += 12.0
                    reasons.append("Field Synergy: Advanced aerial LiDAR and drone survey fleet")
                if any(w in p_domain and w in combined_scope for w in ["cloud", "software", "ai", "mis"]):
                    match_score += 10.0
                    reasons.append("Software Synergy: Enterprise cloud and AI analytics solutions")

                # Multilateral Experience
                if "world bank" in p_domain or "adb" in p_domain or "multilateral" in p_domain:
                    match_score += 10.0
                    reasons.append("Multilateral Experience: Proven track record on donor-financed tenders")

                scored_partners.append({
                    "partner_id": p.id,
                    "name": p.name,
                    "short_name": p.short_name or p.name,
                    "country": p.state or "International",
                    "city": p.city or "Headquarters",
                    "primary_domain": p.primary_domain,
                    "email": p.email,
                    "website": p.website,
                    "match_score": min(round(match_score, 1), 99.0),
                    "selection_reasons": reasons,
                    "synergy_role": f"Partner to lead in-country stakeholder coordination and field surveying in {dev.country or 'project territory'}, while GISFY leads enterprise WebGIS and spatial data platform engineering."
                })

            # Sort by match score descending
            scored_partners.sort(key=lambda x: x["match_score"], reverse=True)
            return scored_partners[:limit]

        finally:
            if should_close:
                db.close()

    def generate_draft_email_for_partner(
        self,
        tender_id: int,
        partner_id: int,
        db: Session
    ) -> models.CollaborationEmail:
        """
        Generate a collaboration outreach email draft for a Devex opportunity and partner.
        Uses approved GISFY template (no 'Project Title:' in body, 2-sentence technical scope,
        executive signature, authentic base64 logo).
        Stored as Draft-Only. Never auto-sent without explicit approval.
        """
        tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
        partner = db.query(models.Partner).filter(models.Partner.id == partner_id).first()

        if not tender or not partner:
            raise ValueError("Tender or Partner not found")

        dev = tender.devex_detail
        sec = dev.project_sector if dev else "Geospatial & Technology Implementation Project"
        comp_name = partner.name

        # Technical scope generation
        scope_text, _, _ = generate_project_technical_scope(
            title=tender.title,
            description=dev.scope_of_work if dev else tender.description,
            project_sector=sec
        )

        subject = f"Exploring JV / Consortium Partnership: {sec}"

        body_text = build_collaboration_email_text(
            project_name=tender.title,
            project_overview=dev.scope_of_work if dev else tender.description,
            is_adb=False,
            sender_name="N C Harika | Business Development Executive",
            sender_email="support@gisfy.co.in",
            sector_phrase=sec,
            technical_scope_paragraph=scope_text
        )

        body_html = build_collaboration_email_html(
            project_name=tender.title,
            project_overview=dev.scope_of_work if dev else tender.description,
            is_adb=False,
            sender_name="N C Harika | Business Development Executive",
            sender_email="support@gisfy.co.in",
            subject_line=subject,
            sector_phrase=sec,
            technical_scope_paragraph=scope_text,
            logo_src=get_gisfy_logo_src()
        )

        # Store as draft in collaboration_emails table
        draft = models.CollaborationEmail(
            tender_id=tender.id,
            partner_id=partner.id,
            recipient_name=f"{partner.name} - Partnership Division",
            recipient_email=partner.email or "bidding@gisfy.co.in",
            company_name=partner.name,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            project_name=tender.title,
            project_overview=dev.scope_of_work if dev else tender.description or tender.title,
            match_score=88.0,
            selection_reason=f"Recommended for {dev.country if dev else 'International'} Consortium in {sec}",
            required_expertise=sec,
            status="Draft",
            approval_status="pending_approval",
            is_draft=True,
            is_test_email=False,
            sender_email="support@gisfy.co.in",
            sender_name="N C Harika | Business Development Executive",
            scope="devex_international"
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft


devex_partner_service = DevexPartnerService()
