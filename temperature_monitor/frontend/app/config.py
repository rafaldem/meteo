"""
Configuration settings for the Temperature Data Dashboard application.
"""

# API Configuration
API_BASE_URL = "http://localhost:5000/api"  # Change to your actual API base URL

# API Endpoints
API_ENDPOINTS = {
    "daily": "/temperature/daily",
    "weekly": "/temperature/weekly",
    "monthly": "/temperature/monthly",
    "yearly": "/temperature/yearly",
}

# Date Formats
DATE_FORMATS = {
    "api": "%Y-%m-%d",  # Format for API requests
    "display": "%Y-%m-%d %H:%M:%S",  # Format for display in the UI
}

# Temperature Units
TEMPERATURE_UNIT = "°C"  # Celsius by default

# Default Time Ranges (in days)
DEFAULT_TIME_RANGES = {"daily": 1, "weekly": 7, "monthly": 30, "yearly": 365}

# Chart Configuration
CHART_CONFIG = {"line_color": "rgb(0, 100, 200)", "grid_color": "rgba(204, 204, 204, 0.2)", "background_color": "white"}

# Threshold Values for Temperature Alerts
TEMPERATURE_THRESHOLDS = {"low_warning": 5.0, "high_warning": 30.0}  # Celsius  # Celsius
