"""
Main Streamlit application for visualizing temperature data from a Raspberry Pi sensor.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# Import custom modules
from config import (
    API_BASE_URL, API_ENDPOINTS, DATE_FORMATS,
    TEMPERATURE_THRESHOLDS, DEFAULT_TIME_RANGES
)
from api_client import TemperatureAPIClient
from data_processor import TemperatureDataProcessor
from visualization import TemperatureVisualizer

# Page configuration
st.set_page_config(
    page_title="Temperature Data Dashboard",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'date_range' not in st.session_state:
    st.session_state.date_range = None
if 'view_type' not in st.session_state:
    st.session_state.view_type = "daily"
if 'show_anomalies' not in st.session_state:
    st.session_state.show_anomalies = False
if 'visualization_type' not in st.session_state:
    st.session_state.visualization_type = "time_series"

class TemperatureDashboardApp:
    """Streamlit application for temperature data visualization."""

    def __init__(self):
        """Initialize the application with APIs and components."""
        self.title = "Raspberry Pi Temperature Monitor"
        self.api_client = TemperatureAPIClient(API_BASE_URL, DATE_FORMATS["api"])
        self.data_processor = TemperatureDataProcessor(
            low_threshold=TEMPERATURE_THRESHOLDS["low_warning"],
            high_threshold=TEMPERATURE_THRESHOLDS["high_warning"]
        )
        self.visualizer = TemperatureVisualizer(theme="plotly", color_scale="Viridis")

    def setup_sidebar(self):
        """Set up the sidebar controls."""
        st.sidebar.title("Controls")

        # Time range selection
        st.sidebar.header("Time Range")

        # View type selector (daily, weekly, monthly, yearly)
        view_type = st.sidebar.selectbox(
            "View Type",
            options=["daily", "weekly", "monthly", "yearly", "custom"],
            index=["daily", "weekly", "monthly", "yearly", "custom"].index(st.session_state.view_type)
        )

        # Update session state if changed
        if view_type != st.session_state.view_type:
            st.session_state.view_type = view_type

        # Date range for custom view
        if view_type == "custom":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now() - timedelta(days=7)
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now()
                )

            # Update session state
            st.session_state.date_range = {
                "start_date": start_date,
                "end_date": end_date
            }

        # Visualization type selector
        st.sidebar.header("Visualization")
        visualization_type = st.sidebar.selectbox(
            "Visualization Type",
            options=[
                "time_series",
                "daily_heatmap",
                "temperature_distribution",
                "monthly_comparison",
                "dashboard"
            ],
            format_func=lambda x: x.replace("_", " ").title(),
            index=["time_series", "daily_heatmap", "temperature_distribution",
                   "monthly_comparison", "dashboard"].index(st.session_state.visualization_type)
        )

        # Update session state if changed
        if visualization_type != st.session_state.visualization_type:
            st.session_state.visualization_type = visualization_type

        # Anomaly detection
        st.sidebar.header("Data Analysis")
        show_anomalies = st.sidebar.checkbox(
            "Detect Anomalies",
            value=st.session_state.show_anomalies
        )

        # Update session state if changed
        if show_anomalies != st.session_state.show_anomalies:
            st.session_state.show_anomalies = show_anomalies

        if show_anomalies:
            anomaly_window = st.sidebar.slider(
                "Anomaly Detection Window",
                min_value=1,
                max_value=24,
                value=12,
                help="Window size for anomaly detection (hours)"
            )

            anomaly_threshold = st.sidebar.slider(
                "Anomaly Z-Score Threshold",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.1,
                help="Z-score threshold for anomaly detection"
            )
        else:
            anomaly_window = 12
            anomaly_threshold = 3.0

        # Data refresh button
        if st.sidebar.button("Refresh Data"):
            st.session_state.data = None
            st.experimental_rerun()

        # Return all settings
        return {
            "view_type": view_type,
            "date_range": st.session_state.date_range,
            "visualization_type": visualization_type,
            "show_anomalies": show_anomalies,
            "anomaly_window": anomaly_window,
            "anomaly_threshold": anomaly_threshold
        }

    def fetch_data(self, settings):
        """
        Fetch data based on the current settings.

        Args:
            settings (dict): The application settings

        Returns:
            pandas.DataFrame: The temperature data
        """
        view_type = settings["view_type"]

        # Return cached data if available
        if st.session_state.data is not None:
            return st.session_state.data

        # Show loading spinner
        with st.spinner(f"Fetching {view_type} temperature data..."):
            try:
                if view_type == "daily":
                    df = self.api_client.get_daily_data()
                elif view_type == "weekly":
                    df = self.api_client.get_weekly_data()
                elif view_type == "monthly":
                    df = self.api_client.get_monthly_data()
                elif view_type == "yearly":
                    df = self.api_client.get_yearly_data()
                elif view_type == "custom" and settings["date_range"] is not None:
                    start_date = settings["date_range"]["start_date"]
                    end_date = settings["date_range"]["end_date"]
                    df = self.api_client.get_custom_range_data(start_date, end_date)
                else:
                    df = pd.DataFrame()  # Empty dataframe if no valid view type

                # Cache the data
                st.session_state.data = df

                return df

            except Exception as e:
                st.error(f"Error fetching data: {str(e)}")

                # For development/testing, create sample data if API fails
                return self.generate_sample_data(view_type)

    def process_data(self, df, settings):
        """
        Process the data based on the current settings.

        Args:
            df (pandas.DataFrame): The raw temperature data
            settings (dict): The application settings

        Returns:
            pandas.DataFrame: The processed data
        """
        if df.empty:
            return df

        # Process data
        processed_df = self.data_processor.process_data(df)

        # Detect anomalies if requested
        if settings["show_anomalies"]:
            processed_df = self.data_processor.detect_anomalies(
                processed_df,
                window=settings["anomaly_window"],
                threshold=settings["anomaly_threshold"]
            )

        return processed_df

    def create_visualization(self, df, settings):
        """
        Create the appropriate visualization based on settings.

        Args:
            df (pandas.DataFrame): The processed data
            settings (dict): The application settings
        """
        if df.empty:
            st.warning("No data available for the selected time range.")
            return

        view_type = settings["view_type"]
        visualization_type = settings["visualization_type"]
        show_anomalies = settings["show_anomalies"]

        # Create appropriate visualization
        if visualization_type == "time_series":
            if show_anomalies and 'is_anomaly' in df.columns:
                fig = self.visualizer.create_anomaly_chart(
                    df,
                    title=f"{view_type.capitalize()} Temperature Data with Anomalies"
                )
            else:
                fig = self.visualizer.create_time_series(
                    df,
                    title=f"{view_type.capitalize()} Temperature Data"
                )

        elif visualization_type == "daily_heatmap":
            fig = self.visualizer.create_daily_heatmap(
                df,
                title=f"Daily Temperature Patterns - {view_type.capitalize()} View"
            )

        elif visualization_type == "temperature_distribution":
            fig = self.visualizer.create_temperature_distribution(
                df,
                title=f"Temperature Distribution - {view_type.capitalize()} View"
            )

        elif visualization_type == "monthly_comparison":
            # For monthly comparison, filter to the current year if we have yearly data
            if view_type == "yearly" and 'timestamp' in df.columns and not df.empty:
                year = df['timestamp'].dt.year.max()
                fig = self.visualizer.create_monthly_comparison(
                    df,
                    year=year,
                    title=f"Monthly Temperature Comparison - {year}"
                )
            else:
                fig = self.visualizer.create_monthly_comparison(
                    df,
                    title=f"Monthly Temperature Comparison - {view_type.capitalize()} View"
                )

        elif visualization_type == "dashboard":
            fig = self.visualizer.create_dashboard(
                df,
                title=f"Temperature Dashboard - {view_type.capitalize()} View"
            )

        else:
            st.error(f"Unsupported visualization type: {visualization_type}")
            return

        # Display the figure
        st.plotly_chart(fig, use_container_width=True)

    def display_statistics(self, df):
        """
        Display statistics for the temperature data.

        Args:
            df (pandas.DataFrame): The processed data
        """
        if df.empty:
            return

        # Calculate statistics
        stats = self.data_processor.calculate_statistics(df)

        if not stats:
            return

        # Display statistics in expandable section
        with st.expander("Temperature Statistics", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Minimum", f"{stats.get('min', 'N/A'):.2f}°C")
                st.metric("Maximum", f"{stats.get('max', 'N/A'):.2f}°C")

            with col2:
                st.metric("Average", f"{stats.get('avg', 'N/A'):.2f}°C")
                st.metric("Median", f"{stats.get('median', 'N/A'):.2f}°C")

            with col3:
                st.metric("Standard Deviation", f"{stats.get('std', 'N/A'):.2f}°C")
                if 'change_rate_per_hour' in stats:
                    st.metric(
                        "Change Rate",
                        f"{stats['change_rate_per_hour']:.3f}°C/hour",
                        delta=f"{stats['change_rate_per_hour']:.2f}"
                    )

            with col4:
                st.metric("Data Points", f"{stats.get('count', 'N/A')}")

                if 'low_alert_count' in stats and 'high_alert_count' in stats:
                    alerts = stats['low_alert_count'] + stats['high_alert_count']
                    st.metric("Alert Count", f"{alerts}")

    def display_raw_data(self, df):
        """
        Display the raw data in an expandable table.

        Args:
            df (pandas.DataFrame): The processed data
        """
        if df.empty:
            return

        with st.expander("View Raw Data", expanded=False):
            # Format timestamp for display if present
            if 'timestamp' in df.columns:
                display_df = df.copy()
                display_df['timestamp'] = display_df['timestamp'].dt.strftime(DATE_FORMATS["display"])
                st.dataframe(display_df)
            else:
                st.dataframe(df)

            # Download button
            st.download_button(
                label="Download Data as CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"temperature_data_{st.session_state.view_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    def generate_sample_data(self, view_type):
        """
        Generate sample data for development/testing when API is not available.

        Args:
            view_type (str): The view type

        Returns:
            pandas.DataFrame: Sample temperature data
        """
        # Set time range based on view type
        if view_type == "daily":
            start_date = datetime.now() - timedelta(days=1)
            freq = "15T"  # 15 minutes
        elif view_type == "weekly":
            start_date = datetime.now() - timedelta(days=7)
            freq = "1H"  # 1 hour
        elif view_type == "monthly":
            start_date = datetime.now() - timedelta(days=30)
            freq = "4H"  # 4 hours
        elif view_type == "yearly":
            start_date = datetime.now() - timedelta(days=365)
            freq = "1D"  # 1 day
        else:  # custom or fallback
            start_date = datetime.now() - timedelta(days=7)
            freq = "1H"  # 1 hour

        # Generate timestamp range
        end_date = datetime.now()
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

        # Generate sample temperature data
        base_temp = 22.0  # Base temperature in Celsius

        # Daily pattern: warmer during day, cooler at night
        daily_pattern = np.sin(np.linspace(0, 2*np.pi, 24)) * 3

        # Seasonal pattern: warmer in summer, cooler in winter
        days_since_jan1 = (date_range.dayofyear - 1) % 365
        seasonal_pattern = np.sin(days_since_jan1 * (2*np.pi/365)) * 5

        # Generate temperatures with patterns and some random noise
        temperatures = []
        for ts in date_range:
            hour_of_day = ts.hour
            day_of_year = (ts.dayofyear - 1) % 365

            temp = base_temp
            temp += daily_pattern[hour_of_day]  # Daily pattern
            temp += seasonal_pattern[day_of_year]  # Seasonal pattern
            temp += np.random.normal(0, 1)  # Random noise

            temperatures.append(round(temp, 2))

        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': date_range,
            'temperature': temperatures
        })

        return df

    def run(self):
        """Run the Streamlit application."""
        st.title(self.title)

        # Setup sidebar and get settings
        settings = self.setup_sidebar()

        # Fetch data
        df = self.fetch_data(settings)

        # Process data
        processed_df = self.process_data(df, settings)

        # Display top cards with current temperature and status
        if not processed_df.empty and 'temperature' in processed_df.columns:
            current_temp = processed_df['temperature'].iloc[-1]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Current Temperature",
                    f"{current_temp:.1f}°C",
                    delta=f"{current_temp - processed_df['temperature'].iloc[-2]:.1f}°C"
                    if len(processed_df) > 1 else None
                )

            with col2:
                avg_temp = processed_df['temperature'].mean()
                st.metric("Average Temperature", f"{avg_temp:.1f}°C")

            with col3:
                min_temp = processed_df['temperature'].min()
                max_temp = processed_df['temperature'].max()
                st.metric("Min / Max", f"{min_temp:.1f}°C / {max_temp:.1f}°C")

        # Create visualization
        self.create_visualization(processed_df, settings)

        # Display statistics
        self.display_statistics(processed_df)

        # Display raw data table
        self.display_raw_data(processed_df)

# Create and run the app
if __name__ == "__main__":
    app = TemperatureDashboardApp()
    app.run()
