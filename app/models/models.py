from sqlalchemy import Column, Integer, String, DateTime, Time
from ..database.database import Base

class StoreStatus(Base):
    __tablename__ = "store_status"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String)
    timestamp_utc = Column(DateTime)
    status = Column(String)

class BusinessHours(Base):
    __tablename__ = "business_hours"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String)
    day_of_week = Column(Integer)
    start_time_local = Column(Time)
    end_time_local = Column(Time)

class Timezone(Base):
    __tablename__ = "timezone"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, unique=True)
    timezone_str = Column(String)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True)
    status = Column(String)  # "Running" or "Complete"
    generated_at = Column(DateTime)
    file_path = Column(String, nullable=True)