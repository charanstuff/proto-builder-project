import time
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_end_to_end_campaign_flow():
    # Step 1: Create a new lead with a unique email.
    unique_email = f"john.doe+{uuid.uuid4()}@example.com"
    lead_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": unique_email
    }
    lead_response = client.post("/api/leads", json=lead_payload)
    assert lead_response.status_code == 200, lead_response.text
    lead = lead_response.json()
    lead_id = lead["id"]
    print("Created lead:", lead)

    # Step 2: Create a new campaign with the newly created lead attached.
    campaign_payload = {
        "name": "Test Campaign",
        "subject": "Test Subject",
        "follow_up_interval": 1,
        "lead_ids": [lead_id]
    }
    campaign_response = client.post("/api/campaigns", json=campaign_payload)
    assert campaign_response.status_code == 200, campaign_response.text
    campaign = campaign_response.json()
    campaign_id = campaign["id"]
    print("Created campaign:", campaign)

    # Step 3: Immediately the API returns a success; the asynchronous Celery task
    # will process the campaign workflow in the background.
    # Wait a few seconds to allow the background workflow to complete.
    time.sleep(3)

    # Step 4: Retrieve campaign details to verify status update.
    campaign_get_response = client.get(f"/api/campaigns/{campaign_id}")
    assert campaign_get_response.status_code == 200, campaign_get_response.text
    updated_campaign = campaign_get_response.json()
    print("Updated campaign:", updated_campaign)
    # Assert that the campaign status is now 'launched'
    assert updated_campaign["status"] == "launched", f"Expected status 'launched', got {updated_campaign['status']}"

    # (Optional) Step 5: Additional endpoints such as analytics or scoring logs
    # could be tested here to confirm that outreach messages and classification logs exist.
