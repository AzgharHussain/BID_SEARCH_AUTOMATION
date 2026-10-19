from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.post("/ingest")
def ingest_tender(payload: schemas.ScraperIngestPayload, db: Session = Depends(get_db)):
    state = db.query(models.State).filter(models.State.name == payload.state_name).first()
    if not state:
        raise HTTPException(status_code=400, detail=f"State {payload.state_name} not found")

    keyword = db.query(models.Keyword).filter(models.Keyword.keyword == payload.keyword).first()
    if not keyword:
        keyword = models.Keyword(keyword=payload.keyword, is_active=True)
        db.add(keyword)
        db.commit()
        db.refresh(keyword)

    tender = db.query(models.Tender).filter(
        models.Tender.state_id == state.id,
        models.Tender.tender_id == payload.tender_id
    ).first()

    if not tender:
        tender = models.Tender(
            state_id=state.id,
            tender_id=payload.tender_id,
            title=payload.title,
            department=payload.department,
            published_date=payload.published_date,
            last_date=payload.last_date,
            portal_tender_url=payload.portal_tender_url,
            description=payload.description,
            status="new"
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)
        is_new = True
    else:
        db.query(models.Document).filter(models.Document.tender_row_id == tender.id).delete()
        db.commit()
        is_new = False
        
    for doc in payload.documents:
        db_doc = models.Document(
            tender_row_id=tender.id,
            file_name=doc.file_name,
            file_type=doc.file_type,
            source_url=doc.source_url,
            local_path=doc.local_path,
            download_status=doc.download_status,
            portal_size_kb=doc.portal_size_kb
        )
        db.add(db_doc)
    db.commit()

    if keyword not in tender.keywords:
        tender.keywords.append(keyword)
        db.commit()

    return {"message": "Ingested successfully", "tender_id": tender.id, "is_new": is_new}

@router.get("", response_model=List[schemas.TenderSchema])
def list_tenders(
    state_id: Optional[int] = None,
    keyword_id: Optional[int] = None,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Tender)

    if state_id:
        query = query.filter(models.Tender.state_id == state_id)
    if status:
        query = query.filter(models.Tender.status == status)
    if min_score is not None:
        query = query.filter(models.Tender.relevance_score >= min_score)
    if start_date:
        query = query.filter(models.Tender.published_date >= start_date)
    if end_date:
        query = query.filter(models.Tender.published_date <= end_date)
    if keyword_id:
        query = query.join(models.Tender.keywords).filter(models.Keyword.id == keyword_id)

    return query.offset(skip).limit(limit).all()

@router.get("/{id}", response_model=schemas.TenderSchema)
def get_tender(id: int, db: Session = Depends(get_db)):
    tender = db.query(models.Tender).filter(models.Tender.id == id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return tender

class TenderUpdate(schemas.BaseModel):
    status: Optional[str] = None
    relevance_score: Optional[float] = None
    relevance_reason: Optional[str] = None

@router.patch("/{id}")
def update_tender(id: int, update_data: TenderUpdate, db: Session = Depends(get_db)):
    tender = db.query(models.Tender).filter(models.Tender.id == id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if update_data.status:
        tender.status = update_data.status
    if update_data.relevance_score is not None:
        tender.relevance_score = update_data.relevance_score
    if update_data.relevance_reason is not None:
        tender.relevance_reason = update_data.relevance_reason
    
    db.commit()
    db.refresh(tender)
    return {"message": "Updated successfully", "tender": tender.id}
