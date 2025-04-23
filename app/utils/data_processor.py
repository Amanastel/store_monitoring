import pandas as pd
import pytz
from datetime import datetime, timedelta
import csv
import os
from sqlalchemy.orm import Session
from ..models.models import StoreStatus, BusinessHours, Timezone
from dateutil import parser

def load_csv_to_db(db: Session):
    try:
        # Ensure data directory exists
        if not os.path.exists('store-monitoring-data'):
            print("Warning: store-monitoring-data directory not found")
            return

        # Create reports directory
        os.makedirs('reports', exist_ok=True)

        # Read CSV files
        store_status_df = pd.read_csv('store-monitoring-data/store_status.csv')
        business_hours_df = pd.read_csv('store-monitoring-data/menu_hours.csv')
        timezone_df = pd.read_csv('store-monitoring-data/timezones.csv')

        # Clear existing data
        db.query(StoreStatus).delete()
        db.query(BusinessHours).delete()
        db.query(Timezone).delete()
        db.commit()

        # Process and insert store status data
        for _, row in store_status_df.iterrows():
            status = StoreStatus(
                store_id=str(row['store_id']),
                timestamp_utc=parser.parse(row['timestamp_utc']),
                status=row['status']
            )
            db.add(status)

        # Process and insert business hours data
        for _, row in business_hours_df.iterrows():
            hours = BusinessHours(
                store_id=str(row['store_id']),
                day_of_week=row['dayOfWeek'],  # Changed from 'day' to 'dayOfWeek'
                start_time_local=parser.parse(row['start_time_local']).time(),
                end_time_local=parser.parse(row['end_time_local']).time()
            )
            db.add(hours)

        # Process and insert timezone data
        for _, row in timezone_df.iterrows():
            tz = Timezone(
                store_id=str(row['store_id']),
                timezone_str=row['timezone_str']
            )
            db.add(tz)

        db.commit()
        print("Successfully loaded data into database")
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        db.rollback()
        raise

def get_store_hours(db: Session, store_id: str, day_of_week: int):
    hours = db.query(BusinessHours).filter(
        BusinessHours.store_id == store_id,
        BusinessHours.day_of_week == day_of_week
    ).first()
    
    if not hours:
        # Return 24/7 hours if no data
        return datetime.strptime('00:00:00', '%H:%M:%S').time(), \
               datetime.strptime('23:59:59', '%H:%M:%S').time()
    return hours.start_time_local, hours.end_time_local

def get_store_timezone(db: Session, store_id: str):
    tz = db.query(Timezone).filter(Timezone.store_id == store_id).first()
    return tz.timezone_str if tz else 'America/Chicago'

def calculate_uptime_downtime(db: Session, store_id: str, current_timestamp: datetime):
    # Initialize intervals
    hour_ago = current_timestamp - timedelta(hours=1)
    day_ago = current_timestamp - timedelta(days=1)
    week_ago = current_timestamp - timedelta(weeks=1)

    # Get store's timezone
    tz_str = get_store_timezone(db, store_id)
    local_tz = pytz.timezone(tz_str)

    # Get store status data
    status_data = db.query(StoreStatus).filter(
        StoreStatus.store_id == store_id,
        StoreStatus.timestamp_utc >= week_ago,
        StoreStatus.timestamp_utc <= current_timestamp
    ).order_by(StoreStatus.timestamp_utc).all()

    # Initialize counters
    uptime_hour = downtime_hour = 0
    uptime_day = downtime_day = 0
    uptime_week = downtime_week = 0

    # Process each status
    prev_status = None
    prev_timestamp = None

    for status in status_data:
        local_time = status.timestamp_utc.replace(tzinfo=pytz.UTC).astimezone(local_tz)
        day_of_week = local_time.weekday()
        
        # Get business hours for the day
        start_time, end_time = get_store_hours(db, store_id, day_of_week)
        
        # Check if current time is within business hours
        if start_time <= local_time.time() <= end_time:
            duration = 0
            if prev_timestamp:
                duration = (status.timestamp_utc - prev_timestamp).total_seconds() / 3600  # in hours
            
            # Update counters based on status
            if status.status == 'active':
                if status.timestamp_utc >= hour_ago:
                    uptime_hour += min(duration, 1) * 60  # Convert to minutes for last hour
                if status.timestamp_utc >= day_ago:
                    uptime_day += min(duration, 24)
                uptime_week += min(duration, 168)  # 168 hours in a week
            else:
                if status.timestamp_utc >= hour_ago:
                    downtime_hour += min(duration, 1) * 60  # Convert to minutes for last hour
                if status.timestamp_utc >= day_ago:
                    downtime_day += min(duration, 24)
                downtime_week += min(duration, 168)

        prev_status = status.status
        prev_timestamp = status.timestamp_utc

    return {
        'store_id': store_id,
        'uptime_last_hour': round(uptime_hour, 2),
        'uptime_last_day': round(uptime_day, 2),
        'uptime_last_week': round(uptime_week, 2),
        'downtime_last_hour': round(downtime_hour, 2),
        'downtime_last_day': round(downtime_day, 2),
        'downtime_last_week': round(downtime_week, 2)
    }

def generate_report(db: Session, report_path: str):
    # Get the maximum timestamp from the data
    max_timestamp = db.query(StoreStatus.timestamp_utc).order_by(
        StoreStatus.timestamp_utc.desc()
    ).first()[0]

    # Get unique store IDs
    store_ids = db.query(StoreStatus.store_id).distinct().all()
    store_ids = [str(store_id[0]) for store_id in store_ids]

    # Generate report data
    report_data = []
    for store_id in store_ids:
        data = calculate_uptime_downtime(db, store_id, max_timestamp)
        report_data.append(data)

    # Write to CSV
    with open(report_path, 'w', newline='') as csvfile:
        fieldnames = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week',
                     'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in report_data:
            writer.writerow(row)