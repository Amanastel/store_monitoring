from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi import FastAPI
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import os
from ..database.database import get_db
from ..models.models import Report
from ..utils.data_processor import generate_report, load_csv_to_db

router = APIRouter()
app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}


@router.post("/trigger_report")
async def trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Generate unique report ID
    report_id = str(uuid.uuid4())
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/{report_id}.csv"
    
    # Create report entry
    report = Report(
        report_id=report_id,
        status="Running",
        generated_at=datetime.utcnow(),
        file_path=report_path
    )
    db.add(report)
    db.commit()

    # Add report generation task to background tasks
    background_tasks.add_task(process_report, db, report_id, report_path)
    
    return {"report_id": report_id}

@router.get("/get_report/{report_id}")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status == "Running":
        return {"status": "Running"}
    
    if report.status == "Failed":
        return {"status": "Failed"}
    
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return {
        "status": "Complete",
        "report_path": report.file_path
    }

def process_report(db: Session, report_id: str, report_path: str):
    try:
        # Generate the report
        generate_report(db, report_path)
        
        # Update report status
        report = db.query(Report).filter(Report.report_id == report_id).first()
        report.status = "Complete"
        report.file_path = report_path
        db.commit()
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        report = db.query(Report).filter(Report.report_id == report_id).first()
        report.status = "Failed"
        db.commit()