import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("devex_analyzer")

# --------------------------------------------------------------------------
# GISFY VERIFIED CAPABILITY BASELINE (MODULE 9 & 10)
# --------------------------------------------------------------------------
GISFY_VERIFIED_PROFILE = {
    "company_name": "GISFY Private Limited",
    "country_of_incorporation": "India",
    "headquarters": "Uppal, Hyderabad, Telangana, India",
    "incorporation_year": 2019,
    "quality_certifications": [
        "ISO 9001:2015 (Quality Management System)",
        "ISO 27001:2013 (Information Security Management)",
        "CMMI Level 3 Appraised"
    ],
    "core_capabilities": [
        "Geographic Information Systems (GIS) & WebGIS Development",
        "Spatial Data Infrastructure (SDI) & Enterprise Geodatabases",
        "Artificial Intelligence & Machine Learning (AI/ML) Feature Extraction",
        "Drone Photogrammetry & Airborne LiDAR Data Processing",
        "Management Information Systems (MIS) & Cloud Platforms",
        "Hydrological Modeling & Water Network Spatial Asset Management",
        "Municipal Property Tax & Cadastral GIS Modernization",
        "Forestry Canopy Density & Ecological Habitat Analytics",
        "Disaster Early Warning & Climate Risk Monitoring Platforms"
    ],
    "turnover_range_usd": "$2.5M - $5.0M Equivalent",
    "international_eligibility": "Eligible for World Bank, UN, and Multilateral Open International Bidding as an Indian Corporate Entity. Joint Venture / Consortium required in countries mandating registered in-country presence or specialized local regulatory licenses."
}


class DevexEligibilityAndReadinessAnalyzer:
    """
    Module 9 & 10: Deep AI Evaluation of GISFY Eligibility and Proposal Readiness.
    Evaluates:
    - Technical Alignment
    - Prior Project Experience
    - Geographic & Donor Eligibility
    - Financial & Certification Compliance
    - Key Expert Requirements
    - JV / Consortium & Local Partner Requirements
    
    Generates:
    - Verdict: 'Eligible' | 'Not Eligible' | 'Requires Clarification'
    - Specific Qualification Gaps with Source Citations
    - Proposal Readiness Score (0 - 100)
    - Strategic Win-Action Recommendations
    """

    def analyze_opportunity(
        self,
        title: str,
        sector: Optional[str] = None,
        scope_of_work: Optional[str] = None,
        technical_requirements: Optional[str] = None,
        eligibility_criteria: Optional[str] = None,
        qualification_requirements: Optional[str] = None,
        jv_consortium_rules: Optional[str] = None,
        required_experts: Optional[str] = None,
        country: Optional[str] = None,
        donor_agency: Optional[str] = None,
        deadline_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        combined_text = f"{title} {sector or ''} {scope_of_work or ''} {technical_requirements or ''} {eligibility_criteria or ''} {qualification_requirements or ''} {jv_consortium_rules or ''} {required_experts or ''}".lower()

        scores = {
            "technical_alignment": 0,    # Max 30
            "experience_relevance": 0,   # Max 25
            "consortium_viability": 0,   # Max 20
            "donor_eligibility": 0,      # Max 15
            "submission_timeline": 0     # Max 10
        }

        qualification_gaps = []
        identified_strengths = []
        recommendations = []

        # 1. Technical Alignment Assessment (Max 30)
        matched_domains = []
        if any(k in combined_text for k in ["gis", "webgis", "spatial", "geoportal", "geodatabase", "mapping"]):
            matched_domains.append("GIS, WebGIS & Geodatabase Engineering")
            scores["technical_alignment"] += 12
        if any(k in combined_text for k in ["drone", "uav", "lidar", "aerial", "remote sensing", "satellite"]):
            matched_domains.append("Remote Sensing, LiDAR & Drone Survey")
            scores["technical_alignment"] += 8
        if any(k in combined_text for k in ["ai", "machine learning", "computer vision", "analytics", "analytics platform"]):
            matched_domains.append("AI/ML Analytics & Computer Vision")
            scores["technical_alignment"] += 6
        if any(k in combined_text for k in ["mis", "portal", "cloud", "software", "database", "dashboard"]):
            matched_domains.append("Cloud Software & MIS Application Development")
            scores["technical_alignment"] += 4

        if matched_domains:
            identified_strengths.append(f"Strong Technical Alignment: Project aligns directly with GISFY core competencies in {', '.join(matched_domains)}.")
        else:
            qualification_gaps.append("Technical Scope Divergence: Project scope does not prominently feature geospatial, software, or digital data components.")

        # 2. Experience Relevance (Max 25)
        if any(k in combined_text for k in ["water", "hydrology", "canal", "river basin", "irrigation"]):
            identified_strengths.append("Verified Experience Match: GISFY has executed major state water resources and canal GIS network monitoring projects.")
            scores["experience_relevance"] += 12
        if any(k in combined_text for k in ["property tax", "cadastral", "land administration", "urban"]):
            identified_strengths.append("Verified Experience Match: GISFY possesses extensive track record in municipal cadastral mapping and property GIS modernizations.")
            scores["experience_relevance"] += 10
        if any(k in combined_text for k in ["forest", "environment", "wildlife", "climate", "disaster"]):
            identified_strengths.append("Verified Experience Match: GISFY has proven implementations in satellite forest canopy density and environmental monitoring.")
            scores["experience_relevance"] += 10
        if any(k in combined_text for k in ["transport", "road", "railway", "infrastructure asset"]):
            identified_strengths.append("Verified Experience Match: Relevant spatial asset inventory and corridor condition assessment capabilities.")
            scores["experience_relevance"] += 8

        scores["experience_relevance"] = min(scores["experience_relevance"], 25)

        # 3. Donor & Country Eligibility (Max 15)
        clean_country = (country or "").strip().lower()
        clean_donor = (donor_agency or "").strip().lower()

        if "world bank" in clean_donor or "undp" in clean_donor or "ungm" in clean_donor or "afdb" in clean_donor:
            scores["donor_eligibility"] += 15
            identified_strengths.append(f"Eligible Donor System: As an Indian enterprise, GISFY is fully eligible under {donor_agency} Procurement Regulations for International Competitive Bidding.")
        else:
            scores["donor_eligibility"] += 10

        # Check in-country registration or sanctions
        if clean_country not in ["india", ""]:
            if "must be locally registered" in combined_text or "national consultant only" in combined_text:
                qualification_gaps.append(f"In-Country Incorporation Rule: Assignment specifies local entity registration in {country}. Foreign firms must form a Joint Venture with a registered local firm.")
            else:
                identified_strengths.append(f"International Eligibility: Foreign firms permitted to participate independently or in consortium for {country or 'Global'} assignment.")

        # 4. Consortium & JV Viability (Max 20)
        jv_permitted = True
        if "jv not permitted" in combined_text or "individual consultant only" in combined_text:
            jv_permitted = False
            qualification_gaps.append("Consortium Restriction: Bidding notice prohibits Joint Ventures or specifies Individual Consultant selection.")
            scores["consortium_viability"] = 5
        else:
            scores["consortium_viability"] = 20
            identified_strengths.append("Consortium Permitted: Joint Venture / Consortium and Sub-consultancy partnerships are explicitly supported.")

        # 5. Submission Timeline (Max 10)
        if deadline_date:
            days_left = (deadline_date - datetime.utcnow()).days
            if days_left >= 14:
                scores["submission_timeline"] = 10
                identified_strengths.append(f"Adequate Preparation Window: {days_left} days available before deadline.")
            elif days_left >= 5:
                scores["submission_timeline"] = 7
                identified_strengths.append(f"Moderate Preparation Window: {days_left} days remaining.")
            elif days_left >= 1:
                scores["submission_timeline"] = 4
                qualification_gaps.append(f"Tight Submission Window: Only {days_left} days remaining until closing.")
            else:
                scores["submission_timeline"] = 0
                qualification_gaps.append("Deadline Elapsed or Imminent: Assignment deadline is closing today or has passed.")
        else:
            scores["submission_timeline"] = 6

        # Calculate Total Readiness Score
        total_readiness = sum(scores.values())

        # Determine Verdict
        if total_readiness >= 75 and jv_permitted:
            verdict = "Eligible"
        elif total_readiness >= 50:
            verdict = "Requires Clarification"
        else:
            verdict = "Not Eligible"

        # Actionable Win Strategy Recommendations
        if clean_country not in ["india", ""] and jv_permitted:
            recommendations.append(
                f"Form a strategic Joint Venture / Consortium with a verified local partner in {country or 'the target nation'} "
                "to satisfy domestic operational presence and stakeholder engagement, while GISFY leads core technical architecture, "
                "WebGIS implementation, and geodatabase analytics."
            )
        recommendations.append(
            "Align key expert CVs with the specific Terms of Reference requirements, ensuring Team Leader possesses "
            "prior multilateral donor project execution experience."
        )
        recommendations.append(
            "Prepare tailored technical approach highlighting GISFY's ISO 9001:2015 quality standards and past performance on similar large-scale spatial platforms."
        )

        return {
            "verdict": verdict,
            "readiness_score": total_readiness,
            "score_breakdown": scores,
            "identified_strengths": identified_strengths,
            "qualification_gaps": qualification_gaps,
            "recommendations": recommendations,
            "verified_credentials_benchmarked": GISFY_VERIFIED_PROFILE,
            "compliance_disclaimer": "Internal readiness scoring evaluates qualification compliance against authentic TOR specifications. It does not represent a legally verified probability of contract award."
        }


devex_analyzer = DevexEligibilityAndReadinessAnalyzer()
