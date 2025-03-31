# Meteorological Monitoring Application Backend
## Overview
This is the backend API service for the Meteorological Monitoring Application. It provides temperature data collected from a Raspberry Pi Zero W with a 1-wire temperature sensor through a set of REST API endpoints.
## Project Structure
``` 
backend/
├── app.py                 # Main Flask application entry point
├── routes.py              # API route definitions
├── models.py              # Database models
├── version.py             # Version information
├── decorators.py          # Custom Flask decorators
├── __init__.py            # Package initialization
├── config.py              # Configuration settings
├── utils/                 # Utility functions
├── tests/                 # Test suite
│   ├── test_api_format.py
│   ├── test_api_performance.py
│   ├── test_end_to_end.py
│   └── test_input_validation.py
├── requirements.txt       # Required Python packages
└── README.md              # Project documentation
```
## Features
- RESTful API for temperature data retrieval
- Multiple data views:
    - Daily temperature data endpoint
    - Weekly temperature data endpoint
    - Monthly temperature data endpoint
    - Yearly temperature data endpoint
    - Custom date range queries

- Data storage using SQLAlchemy ORM
- Input validation for API requests
- Configurable data aggregation methods
- Error handling and logging

## API Endpoints
- `/temperature/daily` - Daily temperature data
- `/temperature/weekly` - Weekly temperature data
- `/temperature/monthly` - Monthly temperature data
- `/temperature/yearly` - Yearly temperature data
- `/temperature/range` - Custom date range temperature data

All endpoints return JSON data with timestamp and temperature fields.
## Requirements
- Python 3.7+
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Werkzeug

## Installation
1. Clone the repository:
``` 
   https://github.com/rafaldem/meteo.git
   cd meteo/backend
```
1. Install the required packages:
``` 
   pip install -r requirements.txt
```
1. Configure your database connection in `config.py`.

## Usage
1. Start the Flask application:
``` 
   python app.py
```
1. The API will be available at `http://localhost:5000/`.

## Development
When developing locally:
- The application includes a test suite with unit tests and end-to-end tests
- Use `pytest` to run the test suite
- Mock data can be generated for testing without a physical temperature sensor

## License
This project is licensed under the MIT License - see the LICENSE file for details.
