# app/routes/outreach/outreach.py
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List

from app.models import SessionLocal, OutreachLog, Campaign, Lead

router = APIRouter()

class OutreachLogResponse(BaseModel):
    id: int
    campaign_id: int
    lead_id: int
    message: str
    sent_at: datetime
    status: str

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/logs", response_model=List[OutreachLogResponse])
def list_outreach_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(OutreachLog).offset(skip).limit(limit).all()
    return logs

class SendOutreachRequest(BaseModel):
    campaign_id: int
    lead_id: int
    message: str

@router.post("/send", response_model=OutreachLogResponse)
def send_outreach(request: SendOutreachRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Simulate sending a message (e.g. via an email API)
    new_log = OutreachLog(
        campaign_id=request.campaign_id,
        lead_id=request.lead_id,
        message=request.message,
        sent_at=datetime.utcnow(),
        status="sent"
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log
