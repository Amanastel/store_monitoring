from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import logging
from .database.database import engine, get_db
from .models import models
from .routers import reports
from .utils.data_processor import load_csv_to_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Store Monitoring API")

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(reports.router)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Starting application...")
        db = next(get_db())
        load_csv_to_db(db)
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.get("/download_report/{report_id}")
async def download_report(report_id: str):
    try:
        return FileResponse(
            path=f"reports/{report_id}.csv",
            filename=f"report_{report_id}.csv",
            media_type="text/csv"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Report not found")