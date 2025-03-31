# Raspberry Pi Temperature Dashboard

A Python-based frontend application for visualizing temperature data collected from a Raspberry Pi Zero W with a 1-wire temperature sensor.

## Project Structure

```
temperature-dashboard/
├── app.py                 # Main Streamlit application
├── api_client.py          # API client for data retrieval
├── config.py              # Configuration settings
├── data_processor.py      # Data processing module
├── visualization.py       # Data visualization module
├── requirements.txt       # Required Python packages
└── README.md              # Project documentation
```

## Features

- Visualize temperature data in daily, weekly, monthly, or yearly views
- Multiple visualization types:
  - Time series charts
  - Daily temperature heatmaps
  - Temperature distribution histograms
  - Monthly comparison box plots
  - Comprehensive dashboard
- Anomaly detection to identify unusual temperature readings
- Statistical analysis of temperature data
- Data export for further analysis
- Responsive user interface with Streamlit

## Requirements

- Python 3.7+
- Streamlit
- Pandas
- NumPy
- Plotly
- Requests

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/temperature-dashboard.git
   cd temperature-dashboard
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure the API endpoint in `config.py` to point to your backend service.

## Usage

1. Start the Streamlit application:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501).

3. Use the sidebar controls to select the view type, date range, and visualization options.

## API Integration

The application integrates with a backend API service that provides temperature data. The API endpoints are configurable in `config.py`. The expected API endpoints are:

- `/temperature/daily` - Daily temperature data
- `/temperature/weekly` - Weekly temperature data
- `/temperature/monthly` - Monthly temperature data
- `/temperature/yearly` - Yearly temperature data
- `/temperature/range` - Custom date range temperature data

The API is expected to return JSON data with at least `timestamp` and `temperature` fields.

## Customization

You can customize various aspects of the application by modifying the `config.py` file:

- API endpoints and base URL
- Date formats for API requests and display
- Temperature thresholds for alerts
- Default time ranges
- Chart configuration settings

## Development

When developing locally without access to the API, the application will generate sample data for testing purposes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
