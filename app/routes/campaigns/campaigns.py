# app/routes/campaigns/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.models import SessionLocal, Campaign, Lead
from app.tasks import process_campaign_workflow_task  # import the Celery task

router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    subject: str
    follow_up_interval: int  # in days
    lead_ids: Optional[List[int]] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    subject: str
    status: str
    created_at: datetime
    lead_ids: List[int] = []

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Instead of directly updating the DB, we now schedule a Celery task.
def launch_campaign_task(campaign_id: int):
    process_campaign_workflow_task.delay(campaign_id)

@router.post("/", response_model=CampaignResponse)
def create_campaign(
    campaign_in: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    new_campaign = Campaign(
        name=campaign_in.name,
        subject=campaign_in.subject,
        follow_up_interval=campaign_in.follow_up_interval,
        status="draft",
        created_at=datetime.utcnow()
    )
    if campaign_in.lead_ids:
        leads = db.query(Lead).filter(Lead.id.in_(campaign_in.lead_ids)).all()
        if not leads:
            raise HTTPException(status_code=404, detail="No leads found with provided ids")
        new_campaign.leads.extend(leads)
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    # Immediately return success to the user.
    # Then, schedule the asynchronous campaign processing via Celery.
    background_tasks.add_task(launch_campaign_task, new_campaign.id)
    response = CampaignResponse.from_orm(new_campaign)
    response.lead_ids = [lead.id for lead in new_campaign.leads]
    return response

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    response = CampaignResponse.from_orm(campaign)
    response.lead_ids = [lead.id for lead in campaign.leads]
    return response
