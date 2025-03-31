"""
Module for processing and analyzing temperature data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TemperatureDataProcessor:
    """Process and analyze temperature data."""

    def __init__(self, low_threshold=None, high_threshold=None):
        """
        Initialize the data processor.

        Args:
            low_threshold (float, optional): Low temperature threshold for alerts
            high_threshold (float, optional): High temperature threshold for alerts
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def process_data(self, df):
        """
        Process raw temperature data.

        Args:
            df (pandas.DataFrame): Raw temperature data with 'timestamp' and 'temperature' columns

        Returns:
            pandas.DataFrame: Processed data with additional metrics
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for processing")
            return df

        try:
            # Create a copy to avoid modifying the original DataFrame
            processed_df = df.copy()

            # Ensure timestamp is in datetime format
            if "timestamp" in processed_df.columns:
                processed_df["timestamp"] = pd.to_datetime(processed_df["timestamp"])

                # Sort by timestamp
                processed_df = processed_df.sort_values("timestamp")

                # Add date components for easier filtering
                processed_df["date"] = processed_df["timestamp"].dt.date
                processed_df["hour"] = processed_df["timestamp"].dt.hour
                processed_df["day_of_week"] = processed_df["timestamp"].dt.day_name()
                processed_df["month"] = processed_df["timestamp"].dt.month_name()
                processed_df["year"] = processed_df["timestamp"].dt.year

            # Add temperature alerts if thresholds are provided
            if "temperature" in processed_df.columns:
                if self.low_threshold is not None:
                    processed_df["low_alert"] = processed_df["temperature"] < self.low_threshold

                if self.high_threshold is not None:
                    processed_df["high_alert"] = processed_df["temperature"] > self.high_threshold

                # Calculate rolling averages
                processed_df["rolling_avg_1h"] = processed_df["temperature"].rolling(window="1H").mean()
                processed_df["rolling_avg_24h"] = processed_df["temperature"].rolling(window="24H").mean()

            return processed_df

        except Exception as e:
            logger.error(f"Error processing temperature data: {str(e)}")
            return df

    def calculate_statistics(self, df):
        """
        Calculate statistics for temperature data.

        Args:
            df (pandas.DataFrame): Temperature data

        Returns:
            dict: Statistics including min, max, avg, std, etc.
        """
        if df.empty or "temperature" not in df.columns:
            return {}

        try:
            stats = {
                "min": df["temperature"].min(),
                "max": df["temperature"].max(),
                "avg": df["temperature"].mean(),
                "median": df["temperature"].median(),
                "std": df["temperature"].std(),
                "count": len(df),
                "start_time": df["timestamp"].min() if "timestamp" in df.columns else None,
                "end_time": df["timestamp"].max() if "timestamp" in df.columns else None,
            }

            # Calculate temperature change rate (per hour)
            if "timestamp" in df.columns and len(df) > 1:
                first_temp = df.iloc[0]["temperature"]
                last_temp = df.iloc[-1]["temperature"]
                first_time = df.iloc[0]["timestamp"]
                last_time = df.iloc[-1]["timestamp"]

                time_diff_hours = (last_time - first_time).total_seconds() / 3600
                if time_diff_hours > 0:
                    stats["change_rate_per_hour"] = (last_temp - first_temp) / time_diff_hours

            # Add temperature threshold alerts count if applicable
            if "low_alert" in df.columns:
                stats["low_alert_count"] = df["low_alert"].sum()

            if "high_alert" in df.columns:
                stats["high_alert_count"] = df["high_alert"].sum()

            return stats

        except Exception as e:
            logger.error(f"Error calculating temperature statistics: {str(e)}")
            return {}

    def resample_data(self, df, frequency="1H"):
        """
        Resample data to a specified frequency.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp' and 'temperature' columns
            frequency (str, optional): Pandas frequency string (e.g., '1H', '1D')

        Returns:
            pandas.DataFrame: Resampled data
        """
        if df.empty or "timestamp" not in df.columns or "temperature" not in df.columns:
            return df

        try:
            # Ensure timestamp is set as index
            df_indexed = df.set_index("timestamp") if df.index.name != "timestamp" else df.copy()

            # Resample data
            resampled = df_indexed["temperature"].resample(frequency).agg(["mean", "min", "max", "std"])
            resampled.columns = ["temperature_mean", "temperature_min", "temperature_max", "temperature_std"]

            # Reset index to convert timestamp back to a column
            resampled = resampled.reset_index()

            return resampled

        except Exception as e:
            logger.error(f"Error resampling temperature data: {str(e)}")
            return df

    def detect_anomalies(self, df, window=12, threshold=3.0):
        """
        Detect anomalies in temperature data using Z-score.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp' and 'temperature' columns
            window (int, optional): Window size for rolling statistics
            threshold (float, optional): Z-score threshold for anomaly detection

        Returns:
            pandas.DataFrame: Data with anomaly flags added
        """
        if df.empty or "temperature" not in df.columns:
            return df

        try:
            # Create a copy to avoid modifying the original DataFrame
            result_df = df.copy()

            # Calculate rolling mean and standard deviation
            rolling_mean = result_df["temperature"].rolling(window=window).mean()
            rolling_std = result_df["temperature"].rolling(window=window).std()

            # Handle cases where std is zero or NA
            rolling_std = rolling_std.replace(0, np.nan)
            rolling_std = rolling_std.fillna(result_df["temperature"].std())

            # Calculate z-scores
            z_scores = (result_df["temperature"] - rolling_mean) / rolling_std

            # Flag anomalies
            result_df["is_anomaly"] = abs(z_scores) > threshold
            result_df["z_score"] = z_scores

            return result_df

        except Exception as e:
            logger.error(f"Error detecting anomalies in temperature data: {str(e)}")
            return df
