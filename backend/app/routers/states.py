from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("", response_model=List[schemas.StateSchema])
def get_states(db: Session = Depends(get_db)):
    return db.query(models.State).order_by(models.State.name.asc()).all()

@router.post("", response_model=schemas.StateSchema)
def create_state(state: schemas.StateCreate, db: Session = Depends(get_db)):
    existing = db.query(models.State).filter(models.State.name == state.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="State already exists")
    new_state = models.State(**state.model_dump())
    db.add(new_state)
    db.commit()
    db.refresh(new_state)
    return new_state
