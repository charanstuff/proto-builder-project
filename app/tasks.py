from celery_app import celery
from app.workflow import process_campaign_workflow

@celery.task(name="process_campaign_workflow_task")
def process_campaign_workflow_task(campaign_id: int):
    process_campaign_workflow(campaign_id)
