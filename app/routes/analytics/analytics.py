# app/routes/analytics/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.models import SessionLocal, Campaign, Lead, Message

router = APIRouter()

class CampaignAnalytics(BaseModel):
    campaign_id: int
    total_leads: int
    launched: bool
    total_messages_sent: int

class LeadsAnalytics(BaseModel):
    total_leads: int
    new_leads: int
    qualified_leads: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/campaigns", response_model=List[CampaignAnalytics])
def get_campaign_analytics(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).all()
    analytics = []
    for camp in campaigns:
        total_leads = len(camp.leads)
        total_messages = db.query(Message).filter(Message.campaign_id == camp.id).count()
        analytics.append(CampaignAnalytics(
            campaign_id=camp.id,
            total_leads=total_leads,
            launched=(camp.status == "launched"),
            total_messages_sent=total_messages
        ))
    return analytics

@router.get("/leads", response_model=LeadsAnalytics)
def get_leads_analytics(db: Session = Depends(get_db)):
    total = db.query(Lead).count()
    new = db.query(Lead).filter(Lead.status == "new").count()
    # Example: qualified if score >= 50
    qualified = db.query(Lead).filter(Lead.score >= 50).count()
    return LeadsAnalytics(
        total_leads=total,
        new_leads=new,
        qualified_leads=qualified
    )
