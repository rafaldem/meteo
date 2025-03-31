import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import json
from config import API_BASE_URL, API_ENDPOINTS, DATE_FORMATS


class TemperatureDataApp:
    """
    A Streamlit application for visualizing temperature data collected from
    a Raspberry Pi Zero W 1-wire temperature sensor.
    """

    def __init__(self):
        """Initialize the application with default settings."""
        self.api_base_url = API_BASE_URL
        self.api_endpoints = API_ENDPOINTS
        self.date_formats = DATE_FORMATS
        self.setup_page()

    def setup_page(self):
        """Configure the initial Streamlit page settings."""
        st.set_page_config(
            page_title="Temperature Data Dashboard", page_icon="🌡️", layout="wide", initial_sidebar_state="expanded"
        )
        st.title("Temperature Data Dashboard")
        st.sidebar.title("Settings")

    def fetch_data(self, view_type, start_date=None, end_date=None):
        """
        Fetch temperature data from the API based on the selected view type.

        Args:
            view_type (str): One of 'daily', 'weekly', 'monthly', 'yearly'
            start_date (str, optional): Start date for custom range
            end_date (str, optional): End date for custom range

        Returns:
            pandas.DataFrame: The temperature data
        """
        try:
            endpoint = self.api_endpoints[view_type]

            params = {}
            if start_date and end_date:
                params["start_date"] = start_date
                params["end_date"] = end_date

            response = requests.get(f"{self.api_base_url}{endpoint}", params=params)

            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)

                # Convert timestamp to datetime
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                return df
            else:
                st.error(f"Error retrieving data: {response.status_code}")
                return pd.DataFrame()

        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return pd.DataFrame()

    def create_visualization(self, df, view_type):
        """
        Create a visualization of the temperature data.

        Args:
            df (pandas.DataFrame): The temperature data
            view_type (str): One of 'daily', 'weekly', 'monthly', 'yearly'

        Returns:
            plotly.graph_objects.Figure: The visualization
        """
        if df.empty:
            st.warning("No data available for the selected time range.")
            return None

        # Create a line plot
        fig = px.line(
            df,
            x="timestamp",
            y="temperature",
            title=f"{view_type.capitalize()} Temperature Data",
            labels={"temperature": "Temperature (°C)", "timestamp": "Time"},
            line_shape="linear",
        )

        # Add a range slider
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list(
                        [
                            dict(count=1, label="1d", step="day", stepmode="backward"),
                            dict(count=7, label="1w", step="day", stepmode="backward"),
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(count=6, label="6m", step="month", stepmode="backward"),
                            dict(step="all"),
                        ]
                    )
                ),
                rangeslider=dict(visible=True),
                type="date",
            )
        )

        # Add min/max/avg annotations
        min_temp = df["temperature"].min()
        max_temp = df["temperature"].max()
        avg_temp = df["temperature"].mean()

        fig.add_annotation(
            text=f"Min: {min_temp:.2f}°C<br>Max: {max_temp:.2f}°C<br>Avg: {avg_temp:.2f}°C",
            align="left",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
        )

        return fig

    def run(self):
        """Run the Streamlit application."""
        # View type selector
        view_type = st.sidebar.selectbox("View Type", options=["daily", "weekly", "monthly", "yearly"], index=0)

        # Date range selection
        use_custom_range = st.sidebar.checkbox("Use Custom Date Range")

        if use_custom_range:
            # Custom date range inputs
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
            with col2:
                end_date = st.date_input("End Date", value=datetime.now())

            start_date_str = start_date.strftime(self.date_formats["api"])
            end_date_str = end_date.strftime(self.date_formats["api"])

            df = self.fetch_data(view_type, start_date_str, end_date_str)
        else:
            # Use default range for the selected view type
            df = self.fetch_data(view_type)

        # Create and display visualization
        fig = self.create_visualization(df, view_type)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # Display data table with expandable detail
        with st.expander("View Raw Data", expanded=False):
            if not df.empty:
                # Format the timestamp for display
                display_df = df.copy()
                display_df["timestamp"] = display_df["timestamp"].dt.strftime(self.date_formats["display"])
                st.dataframe(display_df)
            else:
                st.write("No data available.")

        # Download data option
        if not df.empty:
            st.download_button(
                label="Download Data as CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"temperature_data_{view_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    app = TemperatureDataApp()
    app.run()
