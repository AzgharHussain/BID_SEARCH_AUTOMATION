from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.ScrapeRunSchema])
def get_scrape_runs(db: Session = Depends(get_db)):
    """Return recent scrape runs."""
    return db.query(models.ScrapeRun).order_by(models.ScrapeRun.started_at.desc()).limit(50).all()

@router.post("", response_model=schemas.ScrapeRunSchema)
def log_scrape_run(run: schemas.ScrapeRunCreate, db: Session = Depends(get_db)):
    new_run = models.ScrapeRun(**run.model_dump())
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    return new_run
