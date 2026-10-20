from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import partner_service

router = APIRouter()


@router.get("", response_model=List[schemas.PartnerSchema])
def list_partners(
    search: Optional[str] = Query(None, description="Search by partner name, domain, city, or keyword"),
    domain: Optional[str] = Query(None, description="Filter by primary or secondary domain"),
    state: Optional[str] = Query(None, description="Filter by state location"),
    certification: Optional[str] = Query(None, description="Filter by certification or empanelment"),
    status: Optional[str] = Query(None, description="Filter by partner status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve all registered collaboration partners with optional multi-facet filtering."""
    return partner_service.get_all_partners(
        db=db,
        search=search,
        domain=domain,
        state=state,
        certification=certification,
        status=status,
        skip=skip,
        limit=limit
    )


@router.get("/stats/summary")
def get_collaboration_statistics(db: Session = Depends(get_db)):
    """Summary analytics regarding collaboration partners and active tender consortiums."""
    return partner_service.get_collaboration_stats(db)


@router.get("/search-by-tender/{tender_id}")
def search_partners_for_tender_endpoint(
    tender_id: int,
    query: Optional[str] = Query(None, description="Optional text query to narrow results"),
    domain: Optional[str] = Query(None, description="Optional domain filter"),
    min_score: Optional[float] = Query(80.0, description="Minimum match score threshold (defaults to 80.0% for high matches)"),
    db: Session = Depends(get_db)
):
    """
    Search and rank collaboration partners specifically matched for a tender.
    Returns high matches (score >= 80% by default), tender requirement synergies, and 'why needed' rationale.
    """
    res = partner_service.search_partners_for_tender(
        db=db,
        tender_id=tender_id,
        query_str=query,
        domain_filter=domain,
        min_score=min_score
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/{id}", response_model=schemas.PartnerSchema)
def get_partner_details(id: int, db: Session = Depends(get_db)):
    """Get full details of a specific collaboration partner."""
    partner = db.query(models.Partner).filter(models.Partner.id == id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner


@router.post("", response_model=schemas.PartnerSchema)
def create_new_partner(payload: schemas.PartnerCreate, db: Session = Depends(get_db)):
    """Register a new collaboration partner profile in the database."""
    partner = models.Partner(**payload.model_dump())
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.put("/{id}", response_model=schemas.PartnerSchema)
def update_partner_details(id: int, payload: schemas.PartnerUpdate, db: Session = Depends(get_db)):
    """Update details of an existing collaboration partner."""
    partner = db.query(models.Partner).filter(models.Partner.id == id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(partner, key, value)

    db.commit()
    db.refresh(partner)
    return partner


@router.delete("/{id}")
def delete_partner(id: int, db: Session = Depends(get_db)):
    """Delete a partner profile."""
    partner = db.query(models.Partner).filter(models.Partner.id == id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")

    # Clean up tender collaboration links first
    db.query(models.TenderCollaboration).filter(models.TenderCollaboration.partner_id == id).delete()
    db.delete(partner)
    db.commit()
    return {"message": "Partner deleted successfully", "id": id}


@router.post("/collaboration-status")
def update_collaboration_status(payload: schemas.TenderCollaborationStatusUpdate, db: Session = Depends(get_db)):
    """Update consortium / JV collaboration status between a tender and a partner."""
    collab = partner_service.update_tender_collaboration(
        db=db,
        tender_id=payload.tender_id,
        partner_id=payload.partner_id,
        status=payload.status,
        notes=payload.notes
    )
    return {
        "status": "success",
        "tender_id": collab.tender_id,
        "partner_id": collab.partner_id,
        "collaboration_status": collab.status,
        "notes": collab.notes,
        "updated_at": collab.updated_at.isoformat() if collab.updated_at else None
    }


@router.post("/initiate-outreach", response_model=schemas.OutreachProposalResponse)
def initiate_partner_outreach(payload: schemas.OutreachProposalRequest, db: Session = Depends(get_db)):
    """Generate official Letter of Intent (LOI) & JV proposal for a tender-partner pairing."""
    try:
        return partner_service.generate_outreach_proposal(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-outreach-email")
def send_partner_outreach_email_endpoint(
    payload: schemas.CollaborationEmailDispatchRequest,
    db: Session = Depends(get_db)
):
    """Dispatch official Collaboration LOI email to team and partner with HTML archiving."""
    try:
        return partner_service.send_collaboration_outreach_email(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch collaboration email: {e}")

