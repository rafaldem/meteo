# Meteorological Monitoring Application

A comprehensive system for collecting, storing, and visualizing temperature data from a Raspberry Pi Zero W with a 1-wire temperature sensor.

## Project Overview

This project provides a complete solution for temperature monitoring, including:

- Backend API service for storing and retrieving temperature data
- Frontend dashboard for visualizing temperature trends
- Authentication system for secure access
- Admin interface for system management
- Docker support for easy deployment

## Project Structure

```
temperature_monitor/
├── backend/                 # Flask-based API service
│   ├── app/                 # Core application code
│   │   ├── __init__.py      # Application initialization
│   │   ├── admin/           # Admin routes and functionality
│   │   ├── api/             # API routes for temperature data
│   │   ├── auth/            # Authentication routes
│   │   ├── config.py        # Configuration settings
│   │   ├── models.py        # Database models
│   │   ├── tests/           # Comprehensive test suite
│   │   └── utils/           # Utility functions
│   ├── Dockerfile           # Backend container configuration
│   └── version.py           # Version information
├── frontend/                # Streamlit-based dashboard
│   ├── app/                 # Frontend application code
│   │   ├── api_client.py    # Client for backend API
│   │   ├── app.py           # Main Streamlit application
│   │   ├── config.py        # Configuration settings
│   │   ├── data_processor.py # Data processing module
│   │   ├── main.py          # Entry point
│   │   └── visualization.py # Data visualization components
│   ├── Dockerfile           # Frontend container configuration
│   └── tests/               # Frontend tests
├── scripts/                 # Utility scripts
│   ├── temp/                # Scripts for temperature sensor readings
│   └── version_updater/     # Version management utilities
├── docker-compose.local.yml # Local development configuration
└── requirements.txt         # Project dependencies
```

## Features

### Backend API Service

- RESTful API endpoints for temperature data retrieval
- JWT-based authentication system with user roles
- Multiple data views:
  - Daily temperature data
  - Weekly temperature data
  - Monthly temperature data
  - Yearly temperature data
  - Custom date range queries
- Data persistence using SQLAlchemy ORM
- Comprehensive input validation
- Error handling and logging
- Admin functionality for system configuration and user management

### Frontend Dashboard

- Interactive visualizations of temperature data:
  - Time series charts
  - Daily temperature heatmaps
  - Temperature distribution histograms
  - Monthly comparison box plots
  - Comprehensive dashboard view
- Anomaly detection to identify unusual temperature readings
- Statistical analysis of temperature data
- Data export functionality
- Responsive user interface built with Streamlit
- Customizable themes and layouts

## Requirements

- Python 3.7+
- Docker and Docker Compose (for containerized deployment)
- Raspberry Pi with 1-wire temperature sensor (for data collection)

## Installation

### Docker Installation (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/rafaldem/meteo.git
   cd meteo
   ```

2. Configure environment variables by creating `.env` file based on `.env.example`

3. Start the application using Docker Compose:
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```

4. Access the frontend at http://localhost:3000 and the backend API at http://localhost:8000

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rafaldem/meteo.git
   cd meteo
   ```

2. Install backend dependencies:
   ```bash
   cd temperature_monitor/backend
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd ../frontend
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   cd ../backend
   python app.py
   ```

5. Start the frontend application:
   ```bash
   cd ../frontend
   streamlit run app/app.py
   ```

## Setting Up the Raspberry Pi Sensor

1. Connect the 1-wire temperature sensor to your Raspberry Pi following the manufacturer's instructions.

2. Enable the 1-wire interface on your Raspberry Pi:
   ```bash
   sudo raspi-config
   # Navigate to Interfacing Options > 1-Wire > Yes
   ```

3. Install the required dependencies on the Pi:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip
   pip3 install requests
   ```

4. Deploy the data collection script:
   ```bash
   # Copy the script to the Pi
   scp temperature_monitor/scripts/temp/example_sensor_script.py pi@raspberry-pi-ip:~/
   ```

5. Set up a cron job to run the script at regular intervals:
   ```bash
   # Schedule to run every 5 minutes
   crontab -e
   */5 * * * * python3 ~/example_sensor_script.py
   ```

## API Endpoints

The backend provides these key endpoints:

- **Authentication:**
  - `POST /auth/register` - Register a new user
  - `POST /auth/login` - Login and receive access tokens
  - `POST /auth/refresh` - Refresh access token
  - `GET /auth/profile` - Get user profile

- **Temperature Data:**
  - `GET /api/temperature/{sensor_id}?timeframe=daily` - Get daily temperature data
  - `GET /api/temperature/{sensor_id}?timeframe=weekly` - Get weekly temperature data
  - `GET /api/temperature/{sensor_id}?timeframe=monthly` - Get monthly temperature data
  - `GET /api/temperature/{sensor_id}?timeframe=yearly` - Get yearly temperature data
  - `POST /api/temperature` - Add new temperature reading (admin only)
  - `GET /api/sensors` - Get list of available sensors

- **Admin:**
  - `GET /admin/users` - Get all users (admin only)
  - `PUT /admin/users/{user_id}` - Update user (admin only)
  - `DELETE /admin/users/{user_id}` - Delete user (admin only)
  - `GET /admin/settings` - Get application settings
  - `POST /admin/settings` - Add setting (admin only)
  - `PUT /admin/settings/{key}` - Update setting

## Development

### Running Tests

1. Backend Tests:
   ```bash
   cd temperature_monitor/backend
   pytest
   ```

2. Frontend Tests:
   ```bash
   cd temperature_monitor/frontend
   pytest
   ```

### Version Management

The project includes a version management utility to coordinate versions across components:

```bash
cd temperature_monitor/scripts/version_updater
python update_version.py --component both --bump-type patch
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.