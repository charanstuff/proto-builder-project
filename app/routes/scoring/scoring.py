# app/routes/scoring/scoring.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List
from app.models import SessionLocal, ClassificationLog, Lead

router = APIRouter()

class ClassificationLogResponse(BaseModel):
    id: int
    lead_id: int
    classification_result: str
    score: int
    timestamp: datetime

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ReclassifyRequest(BaseModel):
    new_classification: str
    new_score: int

@router.post("/reclassify/{lead_id}", response_model=ClassificationLogResponse)
def reclassify_lead(lead_id: int, req: ReclassifyRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    # Update lead score (dummy implementation)
    lead.score = req.new_score
    classification_entry = ClassificationLog(
        lead_id=lead_id,
        classification_result=req.new_classification,
        score=req.new_score,
        timestamp=datetime.utcnow()
    )
    db.add(classification_entry)
    db.commit()
    db.refresh(classification_entry)
    return classification_entry

@router.get("/logs", response_model=List[ClassificationLogResponse])
def list_classification_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(ClassificationLog).offset(skip).limit(limit).all()
    return logs
