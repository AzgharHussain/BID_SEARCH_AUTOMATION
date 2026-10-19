from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.KeywordSchema])
def get_keywords(db: Session = Depends(get_db)):
    return db.query(models.Keyword).all()

@router.post("", response_model=schemas.KeywordSchema)
def create_keyword(keyword: schemas.KeywordCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Keyword).filter(models.Keyword.keyword == keyword.keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    new_keyword = models.Keyword(**keyword.model_dump())
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)
    return new_keyword
