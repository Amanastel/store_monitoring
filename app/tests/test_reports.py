import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.main import app
from app.database.database import get_db, Base, engine
from app.utils.data_processor import load_csv_to_db
from sqlalchemy.orm import Session

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = Session(engine)
    
    # Load CSV data into database
    load_csv_to_db(db)
    
    yield
    
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

def test_trigger_report():
    response = client.post("/trigger_report")
    assert response.status_code == 200
    assert "report_id" in response.json()
    report_id = response.json()["report_id"]
    assert isinstance(report_id, str)

def test_get_report_not_found():
    response = client.get("/get_report/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Report not found"

def test_get_report_running():
    # First trigger a report
    response = client.post("/trigger_report")
    report_id = response.json()["report_id"]
    
    # Immediately check its status
    response = client.get(f"/get_report/{report_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "Running"

def test_complete_report_flow():
    # Trigger a report
    response = client.post("/trigger_report")
    report_id = response.json()["report_id"]
    
    # Wait for the report to complete (might take a few seconds)
    import time
    max_wait = 30  # Maximum wait time in seconds
    wait_time = 0
    while wait_time < max_wait:
        response = client.get(f"/get_report/{report_id}")
        if response.json()["status"] == "Complete":
            break
        time.sleep(1)
        wait_time += 1
    
    assert response.status_code == 200
    assert response.json()["status"] == "Complete"
    assert "report_path" in response.json()
    assert os.path.exists(response.json()["report_path"])