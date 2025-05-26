"""
Module for creating visualizations of temperature data.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TemperatureVisualizer:
    """Create visualizations for temperature data."""

    def __init__(self, theme="plotly", color_scale="Viridis"):
        """
        Initialize the visualizer.

        Args:
            theme (str, optional): Plotly theme
            color_scale (str, optional): Color scale for visualizations
        """
        self.theme = theme
        self.color_scale = color_scale
        self.default_layout = {
            "template": theme,
            "margin": {"l": 50, "r": 50, "b": 50, "t": 50, "pad": 4},
            "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02},
            "hovermode": "closest",
        }

    def create_time_series(self, df, title="Temperature Time Series"):
        """
        Create a time series visualization of temperature data.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp' and 'temperature' columns
            title (str, optional): Chart title

        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if df.empty or "timestamp" not in df.columns or "temperature" not in df.columns:
            logger.warning("Cannot create time series: missing data or required columns")
            return go.Figure()

        try:
            fig = px.line(
                df,
                x="timestamp",
                y="temperature",
                title=title,
                labels={"temperature": "Temperature (°C)", "timestamp": "Time"},
                line_shape="linear",
            )

            # Update layout with default settings
            fig.update_layout(**self.default_layout)

            # Add range selector
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list(
                            [
                                dict(count=1, label="1h", step="hour", stepmode="backward"),
                                dict(count=6, label="6h", step="hour", stepmode="backward"),
                                dict(count=12, label="12h", step="hour", stepmode="backward"),
                                dict(count=1, label="1d", step="day", stepmode="backward"),
                                dict(count=7, label="1w", step="day", stepmode="backward"),
                                dict(step="all"),
                            ]
                        )
                    ),
                    rangeslider=dict(visible=True),
                    type="date",
                )
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating time series visualization: {str(e)}")
            return go.Figure()

    def create_daily_heatmap(self, df, title="Daily Temperature Heatmap"):
        """
        Create a heatmap showing temperature patterns across hours and days.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp' and 'temperature' columns
            title (str, optional): Chart title

        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if df.empty or "timestamp" not in df.columns or "temperature" not in df.columns:
            logger.warning("Cannot create heatmap: missing data or required columns")
            return go.Figure()

        try:
            # Extract hour and day from timestamp
            df_copy = df.copy()
            df_copy["hour"] = df_copy["timestamp"].dt.hour
            df_copy["day"] = df_copy["timestamp"].dt.day_name()

            # Compute average temperature by hour and day
            pivot_table = df_copy.pivot_table(values="temperature", index="day", columns="hour", aggfunc="mean")

            # Reorder days of week
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot_table = pivot_table.reindex(days_order)

            # Create heatmap
            fig = px.imshow(
                pivot_table,
                labels=dict(x="Hour of Day", y="Day of Week", color="Temperature (°C)"),
                x=list(range(24)),
                y=days_order,
                color_continuous_scale=self.color_scale,
                title=title,
            )

            # Update layout with default settings
            fig.update_layout(**self.default_layout)

            return fig

        except Exception as e:
            logger.error(f"Error creating daily heatmap visualization: {str(e)}")
            return go.Figure()

    def create_temperature_distribution(self, df, title="Temperature Distribution"):
        """
        Create a histogram showing the distribution of temperature values.

        Args:
            df (pandas.DataFrame): Temperature data with 'temperature' column
            title (str, optional): Chart title

        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if df.empty or "temperature" not in df.columns:
            logger.warning("Cannot create histogram: missing data or required columns")
            return go.Figure()

        try:
            fig = px.histogram(
                df,
                x="temperature",
                title=title,
                labels={"temperature": "Temperature (°C)", "count": "Frequency"},
                nbins=30,
                marginal="box",
            )

            # Add a vertical line for the mean
            mean_temp = df["temperature"].mean()
            fig.add_vline(
                x=mean_temp,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {mean_temp:.2f}°C",
                annotation_position="top right",
            )

            # Update layout with default settings
            fig.update_layout(**self.default_layout)

            return fig

        except Exception as e:
            logger.error(f"Error creating temperature distribution visualization: {str(e)}")
            return go.Figure()

    def create_dashboard(self, df, title="Temperature Dashboard"):
        """
        Create a comprehensive dashboard with multiple visualizations.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp' and 'temperature' columns
            title (str, optional): Dashboard title

        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if df.empty or "timestamp" not in df.columns or "temperature" not in df.columns:
            logger.warning("Cannot create dashboard: missing data or required columns")
            return go.Figure()

        try:
            # Create a figure with subplots
            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    "Temperature Time Series",
                    "Daily Temperature Pattern",
                    "Temperature Distribution",
                    "Temperature Statistics",
                ),
                specs=[[{"type": "scatter"}, {"type": "heatmap"}], [{"type": "histogram"}, {"type": "table"}]],
            )

            # 1. Time Series (top left)
            fig.add_trace(
                go.Scatter(x=df["timestamp"], y=df["temperature"], mode="lines", name="Temperature"), row=1, col=1
            )

            # 2. Daily Pattern Heatmap (top right)
            # Extract hour and day from timestamp
            df_copy = df.copy()
            df_copy["hour"] = df_copy["timestamp"].dt.hour
            df_copy["day"] = df_copy["timestamp"].dt.day_name()

            # Compute average temperature by hour and day
            pivot_data = df_copy.pivot_table(values="temperature", index="day", columns="hour", aggfunc="mean")

            # Reorder days of week
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

            # If we have data for all days, reorder them
            if all(day in pivot_data.index for day in days_order):
                pivot_data = pivot_data.reindex(days_order)

            # Convert pivot table to the format needed for heatmap
            z_data = pivot_data.values
            x_data = pivot_data.columns.tolist()
            y_data = pivot_data.index.tolist()

            fig.add_trace(
                go.Heatmap(
                    z=z_data,
                    x=x_data,
                    y=y_data,
                    colorscale=self.color_scale,
                    colorbar=dict(title="Temp (°C)"),
                    hovertemplate="Hour: %{x}<br>Day: %{y}<br>Temp: %{z:.1f}°C<extra></extra>",
                ),
                row=1,
                col=2,
            )

            # 3. Temperature Distribution (bottom left)
            fig.add_trace(go.Histogram(x=df["temperature"], nbinsx=30, name="Distribution"), row=2, col=1)

            # Add a vertical line for the mean
            mean_temp = df["temperature"].mean()
            fig.add_vline(x=mean_temp, line_dash="dash", line_color="red", row=2, col=1)

            # 4. Statistics Table (bottom right)
            stats = {
                "Statistic": ["Minimum", "Maximum", "Mean", "Median", "Std Dev", "Count"],
                "Value": [
                    f"{df['temperature'].min():.2f}°C",
                    f"{df['temperature'].max():.2f}°C",
                    f"{df['temperature'].mean():.2f}°C",
                    f"{df['temperature'].median():.2f}°C",
                    f"{df['temperature'].std():.2f}°C",
                    f"{len(df)}",
                ],
            }

            fig.add_trace(
                go.Table(
                    header=dict(values=list(stats.keys()), fill_color="paleturquoise", align="left"),
                    cells=dict(values=[stats["Statistic"], stats["Value"]], fill_color="lavender", align="left"),
                ),
                row=2,
                col=2,
            )

            # Update layout with title and default settings
            fig.update_layout(title_text=title, height=800, **self.default_layout)

            # Update xaxis for time series
            fig.update_xaxes(title_text="Time", row=1, col=1)
            fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)

            # Update xaxis for heatmap
            fig.update_xaxes(title_text="Hour of Day", row=1, col=2)
            fig.update_yaxes(title_text="Day of Week", row=1, col=2)

            # Update xaxis for histogram
            fig.update_xaxes(title_text="Temperature (°C)", row=2, col=1)
            fig.update_yaxes(title_text="Frequency", row=2, col=1)

            return fig

        except Exception as e:
            logger.error(f"Error creating dashboard visualization: {str(e)}")
            return go.Figure()

    def create_monthly_comparison(self, df, year=None, title="Monthly Temperature Comparison"):
        """
        Create a box plot comparing temperature distributions across months.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp' and 'temperature' columns
            year (int, optional): Year to filter for (if None, uses all data)
            title (str, optional): Chart title

        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if df.empty or "timestamp" not in df.columns or "temperature" not in df.columns:
            logger.warning("Cannot create monthly comparison: missing data or required columns")
            return go.Figure()

        try:
            # Create a copy and extract month
            df_copy = df.copy()
            df_copy["month"] = df_copy["timestamp"].dt.month_name()
            df_copy["year"] = df_copy["timestamp"].dt.year

            # Filter by year if specified
            if year is not None:
                df_copy = df_copy[df_copy["year"] == year]
                title = f"{title} - {year}"

            # Create box plot
            month_order = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]

            fig = px.box(
                df_copy,
                x="month",
                y="temperature",
                title=title,
                labels={"temperature": "Temperature (°C)", "month": "Month"},
                category_orders={"month": month_order},
            )

            # Add a line connecting the mean values
            monthly_means = df_copy.groupby("month")["temperature"].mean().reindex(month_order)

            fig.add_trace(
                go.Scatter(
                    x=monthly_means.index,
                    y=monthly_means.values,
                    mode="lines+markers",
                    name="Monthly Mean",
                    line=dict(color="red", width=2),
                    marker=dict(size=8, color="red"),
                )
            )

            # Update layout with default settings
            fig.update_layout(**self.default_layout)

            return fig

        except Exception as e:
            logger.error(f"Error creating monthly comparison visualization: {str(e)}")
            return go.Figure()

    def create_anomaly_chart(self, df, title="Temperature Anomalies"):
        """
        Create a visualization highlighting temperature anomalies.

        Args:
            df (pandas.DataFrame): Temperature data with 'timestamp', 'temperature', and 'is_anomaly' columns
            title (str, optional): Chart title

        Returns:
            plotly.graph_objects.Figure: Plotly figure object
        """
        if (
            df.empty
            or "timestamp" not in df.columns
            or "temperature" not in df.columns
            or "is_anomaly" not in df.columns
        ):
            logger.warning("Cannot create anomaly chart: missing data or required columns")
            return go.Figure()

        try:
            # Create figure
            fig = go.Figure()

            # Add normal temperature points
            normal_data = df[~df["is_anomaly"]]
            fig.add_trace(
                go.Scatter(
                    x=normal_data["timestamp"],
                    y=normal_data["temperature"],
                    mode="lines",
                    name="Normal",
                    line=dict(color="blue"),
                )
            )

            # Add anomaly points
            anomaly_data = df[df["is_anomaly"]]
            fig.add_trace(
                go.Scatter(
                    x=anomaly_data["timestamp"],
                    y=anomaly_data["temperature"],
                    mode="markers",
                    name="Anomalies",
                    marker=dict(color="red", size=10, symbol="circle", line=dict(color="black", width=1)),
                )
            )

            # Update layout
            fig.update_layout(title=title, xaxis_title="Time", yaxis_title="Temperature (°C)", **self.default_layout)

            return fig

        except Exception as e:
            logger.error(f"Error creating anomaly chart visualization: {str(e)}")
            return go.Figure()
