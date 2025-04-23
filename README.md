# Store Monitoring System

A FastAPI-based system that monitors store uptime and downtime, providing detailed reports about store operational status. This system processes store data from multiple sources and generates comprehensive reports about store availability.

## Features

- Real-time store status monitoring
- Report generation with uptime/downtime statistics
- Timezone-aware calculations
- Business hours consideration
- CSV report generation
- RESTful API interface
- SQLite database for data storage
- Automated data processing and interpolation

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd store-monitoring-0
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Prepare the data:
- Place your CSV files in the `store-monitoring-data` directory:
  - `store_status.csv` - Contains store status logs
  - `menu_hours.csv` - Contains store business hours
  - `timezones.csv` - Contains store timezone information

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

### Endpoints

1. **Generate Report**
   - Endpoint: `POST /trigger_report`
   - Description: Triggers the generation of a new store monitoring report
   - Response: 
     ```json
     {
         "report_id": "unique-report-id"
     }
     ```

2. **Check Report Status**
   - Endpoint: `GET /get_report/{report_id}`
   - Description: Retrieves the status of a generated report
   - Response:
     ```json
     {
         "status": "Running|Complete",
         "report_path": "path/to/report.csv"  // Only when status is Complete
     }
     ```

3. **Download Report**
   - Endpoint: `GET /download_report/{report_id}`
   - Description: Downloads the generated CSV report
   - Response: CSV file with store uptime/downtime data

## Report Format

The generated report includes the following information for each store:

- Store ID
- Uptime last hour (in minutes)
- Uptime last day (in hours)
- Uptime last week (in hours)
- Downtime last hour (in minutes)
- Downtime last day (in hours)
- Downtime last week (in hours)

## Data Processing Logic

### Business Hours Processing
- Business hours are extracted from menu_hours.csv
- Stores without specified business hours are considered 24/7 operations
- Default timezone (America/Chicago) is used when not specified

### Status Calculation
- Active status is interpolated between observations
- Only business hours are considered for calculations
- Timezone awareness ensures accurate timing calculations

## Project Structure

```
store_monitoring/
├── app/
│   ├── database/       # Database configuration and models
│   ├── models/         # Data models and schemas
│   ├── routers/        # API route handlers
│   ├── utils/          # Utility functions and data processing
│   └── main.py        # Application entry point
├── store-monitoring-data/
│   ├── menu_hours.csv
│   ├── store_status.csv
│   └── timezones.csv
├── reports/           # Generated report storage
└── requirements.txt   # Project dependencies
```

## Testing

Run the tests using pytest:
```bash
python -m pytest app/tests/
```

## Error Handling

The API implements proper error handling for:
- Invalid report IDs
- Missing data files
- Processing errors
- Database connection issues

## Performance Considerations

- Database indexes for optimized queries
- Efficient data processing algorithms
- Asynchronous report generation
- Proper error handling and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)