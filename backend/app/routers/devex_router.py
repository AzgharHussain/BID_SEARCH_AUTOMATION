import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.db.database import get_db, SessionLocal
from app.models import models
from app.services.devex_connector import devex_connector, CLASSIFICATIONS
from app.services.devex_document_service import devex_document_service
from app.services.devex_analyzer import devex_analyzer
from app.services.devex_partner_service import devex_partner_service
from app.services.devex_sync_service import devex_sync_service
from app.services.procurement_deduplication_service import procurement_deduplication_service

logger = logging.getLogger("devex_router")

router = APIRouter()


# --------------------------------------------------------------------------
# 1. GET ALL DEVEX OPPORTUNITIES (MODULE 5, 7, 15)
# --------------------------------------------------------------------------
@router.get("/opportunities")
def get_devex_opportunities(
    country: Optional[str] = None,
    donor: Optional[str] = None,
    sector: Optional[str] = None,
    category: Optional[str] = None,
    opportunity_type: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Retrieve Devex international procurement opportunities with deep filtering and metadata."""
    devex_state = db.query(models.State).filter(
        (models.State.name == "Devex - Global Procurement Intelligence") | 
        (models.State.platform_type == "devex")
    ).first()

    if not devex_state:
        return {"total": 0, "items": [], "filters": {"countries": [], "donors": [], "sectors": [], "types": []}}

    query = db.query(models.Tender).filter(models.Tender.state_id == devex_state.id)
    query = query.outerjoin(models.DevexOpportunityDetail, models.Tender.id == models.DevexOpportunityDetail.tender_id)
    query = query.outerjoin(models.DevexProposalTrack, models.Tender.id == models.DevexProposalTrack.tender_id)

    if country and country.strip() and country.strip() != "ALL":
        query = query.filter(models.DevexOpportunityDetail.country.ilike(f"%{country.strip()}%"))

    if donor and donor.strip() and donor.strip() != "ALL":
        query = query.filter(models.DevexOpportunityDetail.donor_agency.ilike(f"%{donor.strip()}%"))

    if sector and sector.strip() and sector.strip() != "ALL":
        query = query.filter(models.DevexOpportunityDetail.project_sector.ilike(f"%{sector.strip()}%"))

    if category and category.strip() and category.strip() != "ALL":
        query = query.filter(models.DevexOpportunityDetail.procurement_category.ilike(f"%{category.strip()}%"))

    if opportunity_type and opportunity_type.strip() and opportunity_type.strip() != "ALL":
        query = query.filter(models.DevexOpportunityDetail.opportunity_type == opportunity_type.strip())

    if pipeline_stage and pipeline_stage.strip() and pipeline_stage.strip() != "ALL":
        query = query.filter(models.DevexProposalTrack.pipeline_stage == pipeline_stage.strip())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Tender.title.ilike(term),
                models.Tender.tender_id.ilike(term),
                models.DevexOpportunityDetail.original_procurement_ref.ilike(term),
                models.DevexOpportunityDetail.donor_agency.ilike(term),
                models.DevexOpportunityDetail.country.ilike(term),
                models.DevexOpportunityDetail.project_sector.ilike(term),
                models.DevexOpportunityDetail.scope_of_work.ilike(term)
            )
        )

    total_count = query.distinct().count()
    tenders = query.distinct().order_by(desc(models.Tender.published_date)).offset(offset).limit(limit).all()

    # Available filter values
    all_details = db.query(models.DevexOpportunityDetail).all()
    available_countries = sorted(list(set(d.country for d in all_details if d.country)))
    available_donors = sorted(list(set(d.donor_agency for d in all_details if d.donor_agency)))
    available_sectors = sorted(list(set(d.project_sector for d in all_details if d.project_sector)))
    available_types = sorted(list(set(d.opportunity_type for d in all_details if d.opportunity_type)))

    items = []
    for t in tenders:
        detail = t.devex_detail
        tracker = t.devex_tracker
        docs = t.documents or []
        verified_docs_count = sum(1 for d in docs if d.access_status == "Verified Original")

        # Deadline calculations
        deadline_display = detail.submission_deadline_str if detail else (t.last_date.strftime("%d %b %Y") if t.last_date else "Not Disclosed")
        days_left = (t.last_date - datetime.utcnow()).days if t.last_date else None

        items.append({
            "id": t.id,
            "tender_id": t.tender_id,
            "title": t.title,
            "source": "Devex",
            "donor": detail.donor_agency if detail else "Multilateral Donor",
            "country": detail.country if detail else "Global",
            "region": detail.region if detail else "International",
            "sector": detail.project_sector if detail else "Geospatial & Technology",
            "procurement_ref": detail.original_procurement_ref if detail else t.tender_id,
            "opportunity_type": detail.opportunity_type if detail else "Tenders and Open Opportunities",
            "publication_date": t.published_date.strftime("%d %b %Y") if t.published_date else "Recent",
            "closing_date": deadline_display,
            "deadline_ist": t.last_date.isoformat() if t.last_date else None,
            "deadline_timezone": detail.deadline_timezone if detail else "UTC",
            "days_left": days_left,
            "estimated_value": detail.estimated_value if detail else None,
            "currency": detail.currency if detail else "USD",
            "official_tender_url": detail.official_tender_url if detail else t.portal_tender_url,
            "official_donor_website": detail.official_donor_website if detail else "https://www.devex.com",
            "devex_url": detail.devex_url if detail else "https://www.devex.com/funding/r",
            "document_availability": detail.document_availability if detail else "Public",
            "documents_count": len(docs),
            "verified_docs_count": verified_docs_count,
            "integration_mode": detail.integration_mode if detail else "Option B: Business Alert Ingestion",
            "last_verified_at": detail.last_verified_at.isoformat() if detail and detail.last_verified_at else None,
            "pipeline_stage": tracker.pipeline_stage if tracker else "Opportunity Identified",
            "readiness_score": tracker.readiness_score if tracker and tracker.readiness_score else 85.0,
            "gisfy_eligibility": "Eligible" if (tracker and tracker.readiness_score and tracker.readiness_score >= 75) else "Requires Clarification"
        })

    return {
        "total": total_count,
        "items": items,
        "filters": {
            "countries": available_countries,
            "donors": available_donors,
            "sectors": available_sectors,
            "types": available_types
        }
    }


# --------------------------------------------------------------------------
# 2. GET SINGLE OPPORTUNITY DETAIL (MODULE 5, 6, 9)
# --------------------------------------------------------------------------
@router.get("/opportunities/{tender_id}")
def get_devex_opportunity_detail(tender_id: int, db: Session = Depends(get_db)):
    """Retrieve full detail for a single Devex opportunity including documents and AI analysis."""
    tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not tender or not tender.devex_detail:
        raise HTTPException(status_code=404, detail="Devex Opportunity not found")

    detail = tender.devex_detail
    tracker = tender.devex_tracker

    # Authentic Documents List
    docs_list = []
    for d in tender.documents:
        docs_list.append({
            "id": d.id,
            "file_name": d.file_name,
            "file_type": d.file_type,
            "source_url": d.source_url,
            "portal_size_kb": d.portal_size_kb,
            "file_size_bytes": d.file_size_bytes,
            "sha256_hash": d.sha256_hash,
            "doc_category": d.doc_category,
            "access_status": d.access_status,
            "verified": d.verified,
            "download_status": d.download_status,
            "retrieval_timestamp": d.retrieval_timestamp.isoformat() if d.retrieval_timestamp else None
        })

    # AI Eligibility Assessment (Module 9 & 10)
    ai_analysis = devex_analyzer.analyze_opportunity(
        title=tender.title,
        sector=detail.project_sector,
        scope_of_work=detail.scope_of_work,
        technical_requirements=detail.technical_requirements,
        eligibility_criteria=detail.eligibility_criteria,
        qualification_requirements=detail.qualification_requirements,
        jv_consortium_rules=detail.jv_consortium_rules,
        required_experts=detail.required_experts,
        country=detail.country,
        donor_agency=detail.donor_agency,
        deadline_date=tender.last_date
    )

    # Cross-Source Duplicate Linkages (Module 8)
    master_links = db.query(models.MasterOpportunityLink).filter(
        or_(
            models.MasterOpportunityLink.primary_tender_id == tender.id,
            models.MasterOpportunityLink.source_tender_id == tender.id
        )
    ).all()

    linked_duplicates = []
    for ml in master_links:
        if ml.source_tender_id != tender.id:
            dup_t = db.query(models.Tender).filter(models.Tender.id == ml.source_tender_id).first()
            if dup_t:
                linked_duplicates.append({
                    "linked_tender_id": dup_t.id,
                    "title": dup_t.title,
                    "source": dup_t.state.platform_type if dup_t.state else "unknown",
                    "confidence": ml.match_confidence
                })

    return {
        "tender": {
            "id": tender.id,
            "tender_id": tender.tender_id,
            "title": tender.title,
            "published_date": tender.published_date.strftime("%d %b %Y") if tender.published_date else None,
            "last_date": tender.last_date.isoformat() if tender.last_date else None,
            "portal_tender_url": tender.portal_tender_url
        },
        "devex_detail": {
            "devex_id": detail.devex_id,
            "original_procurement_ref": detail.original_procurement_ref,
            "donor_agency": detail.donor_agency,
            "executing_agency": detail.executing_agency,
            "implementing_agency": detail.implementing_agency,
            "country": detail.country,
            "region": detail.region,
            "project_sector": detail.project_sector,
            "procurement_category": detail.procurement_category,
            "opportunity_type": detail.opportunity_type,
            "publication_date_str": detail.publication_date_str,
            "submission_deadline_str": detail.submission_deadline_str,
            "deadline_time": detail.deadline_time,
            "deadline_timezone": detail.deadline_timezone,
            "deadline_ist": detail.deadline_ist.isoformat() if detail.deadline_ist else None,
            "estimated_value": detail.estimated_value,
            "currency": detail.currency,
            "project_duration": detail.project_duration,
            "objectives": detail.objectives,
            "scope_of_work": detail.scope_of_work,
            "technical_requirements": detail.technical_requirements,
            "eligibility_criteria": detail.eligibility_criteria,
            "qualification_requirements": detail.qualification_requirements,
            "jv_consortium_rules": detail.jv_consortium_rules,
            "required_experts": detail.required_experts,
            "official_donor_website": detail.official_donor_website,
            "official_tender_url": detail.official_tender_url,
            "devex_url": detail.devex_url,
            "document_availability": detail.document_availability,
            "integration_mode": detail.integration_mode,
            "last_verified_at": detail.last_verified_at.isoformat() if detail.last_verified_at else None
        },
        "tracker": {
            "pipeline_stage": tracker.pipeline_stage if tracker else "Opportunity Identified",
            "stage_status": tracker.stage_status if tracker else "source_verified",
            "submission_portal": tracker.submission_portal if tracker else detail.official_donor_website,
            "submission_reference": tracker.submission_reference if tracker else detail.original_procurement_ref,
            "lead_partner_name": tracker.lead_partner_name if tracker else "GISFY Private Limited",
            "target_submission_date": tracker.target_submission_date.isoformat() if tracker and tracker.target_submission_date else None,
            "readiness_score": tracker.readiness_score if tracker else ai_analysis["readiness_score"],
            "internal_notes": tracker.internal_notes if tracker else None,
            "history": json.loads(tracker.history_json) if (tracker and tracker.history_json) else []
        },
        "documents": docs_list,
        "ai_analysis": ai_analysis,
        "linked_duplicates": linked_duplicates
    }


# --------------------------------------------------------------------------
# 3. UPDATE PROPOSAL TRACKER (MODULE 14)
# --------------------------------------------------------------------------
@router.post("/opportunities/{tender_id}/tracker")
def update_proposal_tracker(
    tender_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update proposal tracking status, lead partner, and target dates."""
    tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not tender or not tender.devex_detail:
        raise HTTPException(status_code=404, detail="Devex Opportunity not found")

    tracker = tender.devex_tracker
    if not tracker:
        tracker = models.DevexProposalTrack(tender_id=tender.id)
        db.add(tracker)

    new_stage = payload.get("pipeline_stage", tracker.pipeline_stage or "Opportunity Identified")
    stage_notes = payload.get("notes", "Stage updated by GISFY proposal team.")

    tracker.pipeline_stage = new_stage
    tracker.stage_status = payload.get("stage_status", "manual_entry")
    tracker.lead_partner_name = payload.get("lead_partner_name", tracker.lead_partner_name or "GISFY Private Limited")
    tracker.internal_notes = payload.get("internal_notes", tracker.internal_notes)
    
    if payload.get("target_submission_date"):
        try:
            tracker.target_submission_date = datetime.fromisoformat(payload["target_submission_date"].replace("Z", ""))
        except Exception:
            pass

    history = []
    if tracker.history_json:
        try:
            history = json.loads(tracker.history_json)
        except Exception:
            history = []

    history.append({
        "stage": new_stage,
        "timestamp": datetime.utcnow().isoformat(),
        "notes": stage_notes,
        "lead_partner": tracker.lead_partner_name
    })
    tracker.history_json = json.dumps(history)
    tracker.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(tracker)

    return {
        "success": True,
        "tender_id": tender_id,
        "pipeline_stage": tracker.pipeline_stage,
        "stage_status": tracker.stage_status,
        "lead_partner_name": tracker.lead_partner_name,
        "history": history
    }


# --------------------------------------------------------------------------
# 4. PARTNER RECOMMENDATIONS & DRAFT COLLABORATION (MODULE 11)
# --------------------------------------------------------------------------
@router.get("/opportunities/{tender_id}/partners")
def get_partner_recommendations(tender_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """Recommend verified JV / Consortium partners for a Devex international tender."""
    partners = devex_partner_service.recommend_partners_for_opportunity(tender_id=tender_id, limit=limit, db=db)
    return {"tender_id": tender_id, "recommendations": partners}


@router.post("/opportunities/{tender_id}/partners/{partner_id}/draft-email")
def generate_partner_draft_email(tender_id: int, partner_id: int, db: Session = Depends(get_db)):
    """Generate a draft collaboration email using standard GISFY template without sending."""
    try:
        draft = devex_partner_service.generate_draft_email_for_partner(tender_id=tender_id, partner_id=partner_id, db=db)
        return {
            "success": True,
            "draft_id": draft.id,
            "company_name": draft.company_name,
            "subject": draft.subject,
            "body_text": draft.body_text,
            "status": "Draft",
            "message": "Draft created successfully. Auto-send is disabled awaiting approval."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# 5. DOCUMENT DOWNLOADS (MODULE 6)
# --------------------------------------------------------------------------
@router.get("/opportunities/{tender_id}/documents/{doc_id}/download")
def download_document_file(tender_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Download an authentic original tender document."""
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.tender_row_id == tender_id
    ).first()

    if not doc or not doc.local_path or not Path(doc.local_path).exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    file_path = Path(doc.local_path)
    return FileResponse(
        path=str(file_path),
        filename=doc.file_name,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{doc.file_name}"',
            "X-SHA256-Checksum": doc.sha256_hash or ""
        }
    )


@router.get("/opportunities/{tender_id}/download-all-zip")
def download_all_documents_zip(tender_id: int):
    """Download all authentic documents bundled into a ZIP file."""
    zip_path = devex_document_service.generate_all_documents_zip(tender_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="No downloadable documents available for this opportunity")

    return FileResponse(
        path=str(zip_path),
        filename=zip_path.name,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_path.name}"'}
    )


# --------------------------------------------------------------------------
# 6. SYNCHRONIZATION & STATUS (MODULE 12)
# --------------------------------------------------------------------------
@router.post("/sync")
def trigger_devex_sync(
    background_tasks: BackgroundTasks,
    sync_type: str = Query("manual_now"),
    integration_mode: str = Query("Option C: Official Donor Source Enrichment")
):
    """Trigger synchronization of Devex opportunities."""
    res = devex_sync_service.synchronize_opportunities(sync_type=sync_type, integration_mode=integration_mode)
    return res


@router.get("/sync/status")
def get_devex_sync_status(db: Session = Depends(get_db)):
    """Get the latest synchronization status and log metrics."""
    latest_log = db.query(models.DevexSyncLog).order_by(desc(models.DevexSyncLog.started_at)).first()

    devex_state = db.query(models.State).filter(
        (models.State.name == "Devex - Global Procurement Intelligence") | 
        (models.State.platform_type == "devex")
    ).first()

    total_opps = 0
    if devex_state:
        total_opps = db.query(models.Tender).filter(models.Tender.state_id == devex_state.id).count()

    return {
        "is_syncing": (latest_log.status == "running") if latest_log else False,
        "last_sync_status": latest_log.status if latest_log else "idle",
        "last_sync_time": latest_log.finished_at.isoformat() if (latest_log and latest_log.finished_at) else None,
        "started_at": latest_log.started_at.isoformat() if latest_log else None,
        "opportunities_found": latest_log.opportunities_found if latest_log else total_opps,
        "opportunities_added": latest_log.opportunities_added if latest_log else 0,
        "opportunities_updated": latest_log.opportunities_updated if latest_log else 0,
        "documents_downloaded": latest_log.documents_downloaded if latest_log else 0,
        "documents_failed": latest_log.documents_failed if latest_log else 0,
        "total_active_opportunities": total_opps,
        "integration_mode": latest_log.integration_mode if latest_log else "Option B: Business Alert Ingestion",
        "error_message": latest_log.error_message if latest_log else None
    }


# --------------------------------------------------------------------------
# 7. COMPLIANCE & INTEGRATION STATUS (MODULE 2)
# --------------------------------------------------------------------------
@router.get("/compliance-status")
def get_compliance_status():
    """Retrieve Devex access conditions, integration hierarchy status, and active mode."""
    return devex_connector.get_compliance_and_access_status()


# --------------------------------------------------------------------------
# 8. OPTION D: MANUAL IMPORT / PERMITTED EXPORT (MODULE 2)
# --------------------------------------------------------------------------
@router.post("/manual-import")
def manual_import_opportunity(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """Module 2 Option D: Support manual entry or permitted export ingestion."""
    devex_state = db.query(models.State).filter(
        (models.State.name == "Devex - Global Procurement Intelligence") | 
        (models.State.platform_type == "devex")
    ).first()

    title = payload.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    donor = payload.get("donor_agency", "Multilateral Donor")
    country = payload.get("country", "International")
    dev_id = payload.get("devex_id") or f"DEVEX-MANUAL-{int(datetime.utcnow().timestamp())}"
    deadline_str = payload.get("submission_deadline_str", "")
    tz_str = payload.get("deadline_timezone", "UTC")
    ist_dt, resolved_tz = devex_connector.calculate_ist_deadline(deadline_str, tz_str)

    tender = models.Tender(
        state_id=devex_state.id,
        tender_id=dev_id,
        title=title,
        department=f"{donor} / {country}",
        published_date=datetime.utcnow(),
        last_date=ist_dt,
        portal_tender_url=payload.get("official_tender_url", "https://www.devex.com/funding/r"),
        description=payload.get("scope_of_work", title),
        relevance_score=88.0,
        status="new"
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    detail = models.DevexOpportunityDetail(
        tender_id=tender.id,
        devex_id=dev_id,
        original_procurement_ref=payload.get("original_procurement_ref") or dev_id,
        donor_agency=donor,
        country=country,
        region=payload.get("region", "Global"),
        project_sector=payload.get("project_sector", "Geospatial & Technology"),
        procurement_category=payload.get("procurement_category", "Consulting Services"),
        opportunity_type=payload.get("opportunity_type", "Tenders and Open Opportunities"),
        submission_deadline_str=deadline_str,
        deadline_timezone=resolved_tz,
        deadline_ist=ist_dt,
        estimated_value=float(payload.get("estimated_value", 0)) if payload.get("estimated_value") else None,
        currency=payload.get("currency", "USD"),
        scope_of_work=payload.get("scope_of_work", title),
        technical_requirements=payload.get("technical_requirements", ""),
        eligibility_criteria=payload.get("eligibility_criteria", "Open International Bidding"),
        official_donor_website=payload.get("official_donor_website", "https://www.devex.com"),
        official_tender_url=payload.get("official_tender_url", "https://www.devex.com/funding/r"),
        integration_mode="Option D: Manual / Permitted Export",
        document_availability="Uploaded Document Attached"
    )
    db.add(detail)

    track = models.DevexProposalTrack(
        tender_id=tender.id,
        pipeline_stage="Opportunity Identified",
        stage_status="manual_entry",
        submission_portal=payload.get("official_donor_website", "Donor Portal"),
        lead_partner_name="GISFY Private Limited",
        readiness_score=80.0
    )
    db.add(track)
    db.commit()

    return {
        "success": True,
        "tender_id": tender.id,
        "devex_id": dev_id,
        "title": title,
        "integration_mode": "Option D: Manual / Permitted Export"
    }


# --------------------------------------------------------------------------
# 9. UNIFIED PROCUREMENT INTELLIGENCE ENDPOINT (MODULE 7 & 8)
# Combines:
# 1. 29 Indian State Government Tenders
# 2. ADB CMS Opportunities
# 3. Devex Global Opportunities
# With cross-source deduplication filtering.
# --------------------------------------------------------------------------
@router.get("/unified-opportunities")
def get_unified_procurement_opportunities(
    source_filter: str = Query("ALL", description="ALL | STATES | ADB | DEVEX"),
    country: Optional[str] = None,
    sector: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Module 7: Unified Procurement Dashboard endpoint providing multi-source filtering across India, ADB, and Devex."""
    query = db.query(models.Tender).join(models.State)

    if source_filter == "STATES":
        query = query.filter(models.State.id < 30)
    elif source_filter == "ADB":
        query = query.filter(models.State.platform_type == "adb_cms")
    elif source_filter == "DEVEX":
        query = query.filter(models.State.platform_type == "devex")

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Tender.title.ilike(term),
                models.Tender.department.ilike(term),
                models.Tender.tender_id.ilike(term)
            )
        )

    total_count = query.count()
    tenders = query.order_by(desc(models.Tender.published_date)).offset(offset).limit(limit).all()

    items = []
    for t in tenders:
        # Determine source
        src_label = "Indian State Tenders"
        src_code = "STATES"
        donor_client = t.department or (t.state.name if t.state else "Government Authority")
        country_name = "India"
        sector_name = "Technology & Infrastructure"
        readiness = 80.0
        opp_status = "Live"

        if t.state and t.state.platform_type == "adb_cms":
            src_label = "ADB CMS"
            src_code = "ADB"
            country_name = t.adb_detail.country if t.adb_detail else "Multilateral"
            sector_name = t.adb_detail.project_sector if t.adb_detail else "ADB Multilateral Project"
            donor_client = "Asian Development Bank"
            readiness = 88.0
        elif t.state and t.state.platform_type == "devex":
            src_label = "Devex"
            src_code = "DEVEX"
            country_name = t.devex_detail.country if t.devex_detail else "International"
            donor_client = t.devex_detail.donor_agency if t.devex_detail else "Multilateral Donor"
            sector_name = t.devex_detail.project_sector if t.devex_detail else "Global Consulting"
            readiness = t.devex_tracker.readiness_score if (t.devex_tracker and t.devex_tracker.readiness_score) else 85.0

        items.append({
            "id": t.id,
            "tender_id": t.tender_id,
            "title": t.title,
            "source": src_label,
            "source_code": src_code,
            "country": country_name,
            "donor_client": donor_client,
            "sector": sector_name,
            "published_date": t.published_date.strftime("%d %b %Y") if t.published_date else "Recent",
            "closing_date": t.last_date.strftime("%d %b %Y") if t.last_date else "Not Disclosed",
            "opportunity_status": opp_status,
            "gisfy_eligibility": "Eligible" if readiness >= 75 else "Requires Clarification",
            "readiness_score": readiness,
            "documents_count": len(t.documents or []),
            "portal_url": t.portal_tender_url,
            "last_synced": t.updated_at.strftime("%d %b %Y, %H:%M") if t.updated_at else datetime.utcnow().strftime("%d %b %Y, %H:%M")
        })

    return {
        "source_filter": source_filter,
        "total": total_count,
        "items": items
    }
