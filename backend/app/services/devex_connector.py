import os
import re
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from app.db.database import SessionLocal
from app.models import models

logger = logging.getLogger("devex_connector")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "devex_docs"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# GISFY CORE TECHNICAL PRIORITY DOMAINS (MODULE 3)
# --------------------------------------------------------------------------
GISFY_PRIORITY_SECTORS = [
    "Geographic Information Systems (GIS)",
    "WebGIS and Spatial Data Infrastructure (SDI)",
    "Management Information Systems (MIS)",
    "Web and Mobile Application Development",
    "Artificial Intelligence and Machine Learning (AI/ML)",
    "Digital Transformation & Cloud Platforms",
    "Data Analytics & Decision Support Systems",
    "Environmental Information Systems",
    "Disaster Risk Management & Early Warning Systems",
    "Climate Resilience & Adaptation Analytics",
    "Agriculture Information Systems & Crop Monitoring",
    "Forestry and Natural Resource Management",
    "E-Governance & Public Digital Services",
    "Monitoring and Evaluation (M&E) Systems",
    "Land Records Modernization & Cadastral GIS",
    "Water Resources Network & Hydrological Modeling",
    "Urban Infrastructure & Transport GIS"
]

# --------------------------------------------------------------------------
# DEVEX OPPORTUNITY CLASSIFICATIONS (MODULE 4)
# --------------------------------------------------------------------------
CLASSIFICATIONS = {
    "OPEN_TENDER": "Tenders and Open Opportunities",
    "GRANT": "Grants",
    "PROGRAM_REPORT": "Program Reports",
    "FUNDING_ACTIVITY": "Funding Activity",
    "CONTRACT_AWARD": "Contract Awards",
    "SHORTLIST": "Shortlist Announcements"
}

# --------------------------------------------------------------------------
# INTEGRATION HIERARCHY MODES (MODULE 2)
# --------------------------------------------------------------------------
INTEGRATION_MODES = {
    "OPTION_A": {
        "code": "OPTION_A",
        "name": "Option A — Authorized Devex API / Enterprise Data Feed",
        "status": "Awaiting Devex Enterprise Data License / API Key",
        "description": "Requires custom enterprise data agreement with Devex. Disabled by default to prevent unauthorized scraping.",
        "is_active": False
    },
    "OPTION_B": {
        "code": "OPTION_B",
        "name": "Option B — Devex Business Alert Mailbox Ingestion",
        "status": "Operational (Authorized GISFY Mailbox Ingestion)",
        "description": "Ingests daily procurement notices delivered by Devex to GISFY support/bidding mailboxes.",
        "is_active": True
    },
    "OPTION_C": {
        "code": "OPTION_C",
        "name": "Option C — Official Donor Source Direct Enrichment",
        "status": "Operational (Public Donor Procurement Portals)",
        "description": "Directly fetches official tender notices, TORs, and original documents from issuing donor websites (World Bank, UNGM, AfDB, etc.).",
        "is_active": True
    },
    "OPTION_D": {
        "code": "OPTION_D",
        "name": "Option D — Permitted Export / Manual Import",
        "status": "Operational (CSV / JSON / PDF Import)",
        "description": "Permits authorized import of exported search results and official donor tender documents.",
        "is_active": True
    }
}


class DevexConnectorService:
    """
    Devex Global Procurement Intelligence Connector.
    Adheres strictly to permitted integration hierarchy (Options A, B, C, D).
    Zero unauthorized scraping or CAPTCHA circumvention.
    """

    def __init__(self):
        self._config_file = BASE_DIR / ".email_credentials" / "devex_config.json"
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading devex_config.json: {e}")
        return {
            "active_mode": "OPTION_B_AND_C",
            "api_key": None,
            "api_endpoint": "https://api.devex.com/v1",
            "alert_mailbox": "support@gisfy.co.in",
            "auto_sync_enabled": True,
            "sync_interval_hours": 24,
            "priority_keywords": GISFY_PRIORITY_SECTORS
        }

    def save_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        self._config.update(updates)
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)
        return self._config

    def get_compliance_and_access_status(self) -> Dict[str, Any]:
        """Module 2: Return current compliance status, hierarchy status, and active mode."""
        return {
            "platform": "Devex Global Procurement Intelligence",
            "portal_url": "https://www.devex.com/funding/r",
            "active_mode": self._config.get("active_mode", "OPTION_B_AND_C"),
            "compliance_policy": "Strict Zero-Scraping / Official Donor Enrichment Hierarchy Enforced",
            "hierarchy_options": INTEGRATION_MODES,
            "subscription_notes": (
                "Devex restricts automated crawler access under its Terms of Use. "
                "GISFY operates under authorized Option B (Business Alert Ingestion), "
                "Option C (Official Issuing Donor Source Direct Enrichment), and Option D (Permitted Export/Import). "
                "Option A (Direct Enterprise Feed) requires an enterprise API contract with Devex."
            ),
            "priority_sectors": GISFY_PRIORITY_SECTORS,
            "official_donor_sources_supported": [
                "World Bank (WB) eProcurement & Projects Portal",
                "United Nations Global Marketplace (UNGM) & UNDP",
                "African Development Bank (AfDB) Procurement",
                "Millennium Challenge Corporation (MCC)",
                "Inter-American Development Bank (IDB)",
                "Global Environment Facility (GEF)",
                "USAID Development Information Solution"
            ]
        }

    @staticmethod
    def calculate_ist_deadline(
        deadline_str: Optional[str],
        source_timezone: Optional[str] = None
    ) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Preserve original deadline and timezone.
        Convert to IST only when source date and timezone are known.
        """
        if not deadline_str:
            return None, "Not Available from Source"

        clean_tz = (source_timezone or "").strip()
        
        # Try parsing standard formats: "2026-11-25", "25 Nov 2026", "2026-11-25 17:00:00"
        parsed_dt = None
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%d %b %Y %H:%M",
            "%d %b %Y",
            "%d-%m-%Y",
            "%m/%d/%Y"
        ]:
            try:
                parsed_dt = datetime.strptime(deadline_str.strip(), fmt)
                break
            except ValueError:
                continue

        if not parsed_dt:
            return None, clean_tz or "Not Disclosed"

        # If timezone offset is identified, convert to IST (UTC+5:30)
        # EST is UTC-5 (diff = +10.5 hrs to IST)
        # CET is UTC+1 (diff = +4.5 hrs to IST)
        # UTC/GMT (diff = +5.5 hrs to IST)
        # EAT (Nairobi, UTC+3, diff = +2.5 hrs to IST)
        tz_upper = clean_tz.upper()
        if "EST" in tz_upper or "EDT" in tz_upper or "WASHINGTON" in tz_upper or "UTC-5" in tz_upper:
            ist_dt = parsed_dt + timedelta(hours=10, minutes=30)
        elif "CET" in tz_upper or "CEST" in tz_upper or "GENEVA" in tz_upper or "UTC+1" in tz_upper:
            ist_dt = parsed_dt + timedelta(hours=4, minutes=30)
        elif "UTC" in tz_upper or "GMT" in tz_upper:
            ist_dt = parsed_dt + timedelta(hours=5, minutes=30)
        elif "EAT" in tz_upper or "NAIROBI" in tz_upper or "UTC+3" in tz_upper:
            ist_dt = parsed_dt + timedelta(hours=2, minutes=30)
        elif "IST" in tz_upper or "UTC+5:30" in tz_upper:
            ist_dt = parsed_dt
        else:
            # Default to source date without speculative conversion
            ist_dt = parsed_dt

        return ist_dt, clean_tz or "Original Source Timezone"

    def classify_opportunity(
        self,
        title: str,
        opportunity_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Classify Devex intelligence into:
        - Tenders and Open Opportunities (Actionable)
        - Grants (Actionable)
        - Program Reports (Early stage)
        - Funding Activity (Early stage)
        - Contract Awards (Closed/Awarded)
        - Shortlist Announcements (Restricted)
        Returns (Classification Label, IsActionableBidding)
        """
        raw = f"{title} {opportunity_type or ''} {description or ''}".lower()

        if "award" in raw or "contract award" in raw or "winner" in raw:
            return CLASSIFICATIONS["CONTRACT_AWARD"], False
        if "shortlist" in raw or "shortlisted" in raw:
            return CLASSIFICATIONS["SHORTLIST"], False
        if "program report" in raw or "pipeline analysis" in raw:
            return CLASSIFICATIONS["PROGRAM_REPORT"], False
        if "funding activity" in raw or "board approval" in raw or "project appraisal" in raw:
            return CLASSIFICATIONS["FUNDING_ACTIVITY"], False
        if "grant" in raw or "call for proposals" in raw:
            return CLASSIFICATIONS["GRANT"], True

        # Default to Tenders and Open Opportunities
        return CLASSIFICATIONS["OPEN_TENDER"], True


devex_connector = DevexConnectorService()
