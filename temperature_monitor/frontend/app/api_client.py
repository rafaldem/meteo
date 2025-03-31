"""
API client module for retrieving temperature data from the backend service.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TemperatureAPIClient:
    """Client for interacting with the temperature data API."""

    def __init__(self, base_url, date_format="%Y-%m-%d"):
        """
        Initialize the API client.

        Args:
            base_url (str): The base URL for the API
            date_format (str, optional): The date format to use for API requests
        """
        self.base_url = base_url
        self.date_format = date_format
        self.session = requests.Session()

    def _make_request(self, endpoint, params=None):
        """
        Make a request to the API.

        Args:
            endpoint (str): The API endpoint
            params (dict, optional): Query parameters

        Returns:
            dict: The JSON response or None if an error occurred
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None

    def get_daily_data(self, date=None):
        """
        Get temperature data for a specific day.

        Args:
            date (datetime, optional): The date to get data for. Defaults to today.

        Returns:
            pandas.DataFrame: The temperature data
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime(self.date_format)
        data = self._make_request("/temperature/daily", {"date": date_str})

        return self._convert_to_dataframe(data)

    def get_weekly_data(self, end_date=None):
        """
        Get temperature data for the week ending on end_date.

        Args:
            end_date (datetime, optional): The end date. Defaults to today.

        Returns:
            pandas.DataFrame: The temperature data
        """
        if end_date is None:
            end_date = datetime.now()

        start_date = end_date - timedelta(days=7)

        start_date_str = start_date.strftime(self.date_format)
        end_date_str = end_date.strftime(self.date_format)

        data = self._make_request("/temperature/weekly", {"start_date": start_date_str, "end_date": end_date_str})

        return self._convert_to_dataframe(data)

    def get_monthly_data(self, year=None, month=None):
        """
        Get temperature data for a specific month.

        Args:
            year (int, optional): The year. Defaults to current year.
            month (int, optional): The month (1-12). Defaults to current month.

        Returns:
            pandas.DataFrame: The temperature data
        """
        if year is None:
            year = datetime.now().year

        if month is None:
            month = datetime.now().month

        data = self._make_request("/temperature/monthly", {"year": year, "month": month})

        return self._convert_to_dataframe(data)

    def get_yearly_data(self, year=None):
        """
        Get temperature data for a specific year.

        Args:
            year (int, optional): The year. Defaults to current year.

        Returns:
            pandas.DataFrame: The temperature data
        """
        if year is None:
            year = datetime.now().year

        data = self._make_request("/temperature/yearly", {"year": year})

        return self._convert_to_dataframe(data)

    def get_custom_range_data(self, start_date, end_date):
        """
        Get temperature data for a custom date range.

        Args:
            start_date (datetime): The start date
            end_date (datetime): The end date

        Returns:
            pandas.DataFrame: The temperature data
        """
        start_date_str = start_date.strftime(self.date_format)
        end_date_str = end_date.strftime(self.date_format)

        data = self._make_request("/temperature/range", {"start_date": start_date_str, "end_date": end_date_str})

        return self._convert_to_dataframe(data)

    def _convert_to_dataframe(self, data):
        """
        Convert JSON data to a pandas DataFrame.

        Args:
            data (dict or None): The JSON data

        Returns:
            pandas.DataFrame: The converted DataFrame
        """
        if data is None:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Convert timestamp strings to datetime objects if the column exists
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df
