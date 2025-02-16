# app/workflow.py
import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import SessionLocal, Campaign, Lead, OutreachLog, ClassificationLog

def process_campaign_workflow(campaign_id: int):
    """
    Processes a campaign after launch:
      1. Updates campaign status to 'launched'
      2. For each lead in the campaign:
         a. Logs an outreach message (simulate sending)
         b. Simulates a lead response by updating lead score and logging classification
    """
    db: Session = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"Workflow Error: Campaign {campaign_id} not found")
            return

        # Update campaign status to 'launched'
        campaign.status = "launched"
        db.commit()
        print(f"Campaign {campaign.id} status updated to 'launched'.")

        # Process each lead attached to the campaign
        for lead in campaign.leads:
            # Simulate sending an outreach message
            outreach_message = f"Hello {lead.first_name}, check out our campaign '{campaign.name}'."
            outreach_log = OutreachLog(
                campaign_id=campaign.id,
                lead_id=lead.id,
                message=outreach_message,
                sent_at=datetime.utcnow(),
                status="sent"
            )
            db.add(outreach_log)
            print(f"Outreach sent to lead {lead.id}.")

            # Simulate a short delay
            time.sleep(0.1)

            # Simulate processing a lead response: update score and record classification
            new_score = 75  # Dummy score for demonstration
            lead.score = new_score
            classification_log = ClassificationLog(
                lead_id=lead.id,
                classification_result="Interested",
                score=new_score,
                timestamp=datetime.utcnow()
            )
            db.add(classification_log)
            print(f"Lead {lead.id} classified as 'Interested' with score {new_score}.")

        db.commit()
        print("Campaign workflow processing completed.")
    except Exception as e:
        db.rollback()
        print("Error during campaign workflow processing:", e)
    finally:
        db.close()
