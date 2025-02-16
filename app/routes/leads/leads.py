# app/routes/leads/leads.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union
import csv
import io
from datetime import datetime

from app.models import SessionLocal, Lead
from app.config import settings

router = APIRouter()

class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[str] = None
    score: Optional[int] = None

class LeadResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    status: str
    score: int
    created_at: datetime

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[LeadResponse])
def list_leads(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    leads = db.query(Lead).offset(skip).limit(limit).all()
    return leads

@router.post("/", response_model=Union[LeadResponse, List[LeadResponse]])
def create_leads(leads_in: Union[LeadCreate, List[LeadCreate]], db: Session = Depends(get_db)):
    if isinstance(leads_in, list):
        created_leads = []
        for lead_data in leads_in:
            new_lead = Lead(
                first_name=lead_data.first_name,
                last_name=lead_data.last_name,
                email=lead_data.email,
                status="new",
                score=0,
                created_at=datetime.utcnow()
            )
            db.add(new_lead)
            created_leads.append(new_lead)
        db.commit()
        for lead in created_leads:
            db.refresh(lead)
        return created_leads
    else:
        new_lead = Lead(
            first_name=leads_in.first_name,
            last_name=leads_in.last_name,
            email=leads_in.email,
            status="new",
            score=0,
            created_at=datetime.utcnow()
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        return new_lead

@router.post("/upload", response_model=List[LeadResponse])
async def upload_leads(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    csv_data = io.StringIO(content.decode("utf-8"))
    reader = csv.DictReader(csv_data)
    created_leads = []
    for row in reader:
        new_lead = Lead(
            first_name=row.get("first_name", ""),
            last_name=row.get("last_name", ""),
            email=row.get("email", ""),
            status="new",
            score=0,
            created_at=datetime.utcnow()
        )
        db.add(new_lead)
        created_leads.append(new_lead)
    db.commit()
    for lead in created_leads:
        db.refresh(lead)
    return created_leads

@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    update_data = lead_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lead, key, value)
    db.commit()
    db.refresh(lead)
    return lead

@router.delete("/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
    return {"detail": "Lead deleted successfully"}
