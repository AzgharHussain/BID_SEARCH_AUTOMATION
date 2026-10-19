from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.post("", response_model=schemas.ScrapeRunSchema)
def log_scrape_run(run: schemas.ScrapeRunCreate, db: Session = Depends(get_db)):
    new_run = models.ScrapeRun(**run.model_dump())
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    return new_run
