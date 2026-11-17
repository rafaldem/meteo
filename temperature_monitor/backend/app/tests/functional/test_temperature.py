import pytest
import calendar
import json
from datetime import datetime, timedelta

from models import TemperatureReading


def test_add_temperature(client, admin_headers, db_session):
    """Test adding a temperature reading."""

    response = client.post(
        "/api/temperature",
        headers=admin_headers,
        json={"sensor_id": "new-sensor", "temperature": 22.5, "humidity": 55.0},
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["sensor_id"] == "new-sensor"
    assert data["temperature"] == 22.5
    assert data["humidity"] == 55.0

    reading = TemperatureReading.query.filter_by(sensor_id="new-sensor").first()
    assert reading is not None
    assert reading.temperature == 22.5
    assert reading.humidity == 55.0


def test_add_temperature_unauthorized(client, user_headers):
    """Test adding a temperature reading with insufficient permissions."""

    response = client.post(
        "/api/temperature",
        headers=user_headers,
        json={"sensor_id": "new-sensor", "temperature": 22.5, "humidity": 55.0},
    )

    assert response.status_code == 403
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Admin privileges required"


def _get(client, headers, sensor_id, timeframe, day=None):
    url = f"/api/temperature/{sensor_id}?timeframe={timeframe}"
    if day:
        url += f"&date={day:%Y-%m-%d}"
    response = client.get(url, headers=headers)
    assert response.status_code == 200, response.data
    return json.loads(response.data)


def _assert_consistent(entries):
    """Aggregates returned for mocked readings must be internally consistent."""

    for entry in entries:
        assert entry["min_temperature"] <= entry["avg_temperature"] <= entry["max_temperature"]
        assert -40 <= entry["min_temperature"] and entry["max_temperature"] <= 50
        assert 20 <= entry["avg_humidity"] <= 100  # seeder clamps humidity to 20-100 %


def test_get_temperature_daily(client, user_headers, mock_sensor_id):
    """Daily view of a fully seeded day returns one aggregate per hour."""

    yesterday = datetime.now() - timedelta(days=1)
    data = _get(client, user_headers, mock_sensor_id, "daily", yesterday)

    assert data["sensor_id"] == mock_sensor_id
    assert data["timeframe"] == "daily"
    assert len(data["data"]) == 24

    first_entry = data["data"][0]
    for key in ("time_group", "avg_temperature", "min_temperature", "max_temperature", "avg_humidity"):
        assert key in first_entry
    _assert_consistent(data["data"])


def test_get_temperature_daily_defaults_to_today(client, user_headers, mock_sensor_id):
    """Without a date the API returns today's (possibly partial) mocked data."""

    data = _get(client, user_headers, mock_sensor_id, "daily")

    assert data["start_date"].startswith(f"{datetime.now():%Y-%m-%d}")
    assert len(data["data"]) >= 1  # seeded up to "now", so at least the first hour exists
    _assert_consistent(data["data"])


def test_get_temperature_weekly(client, user_headers, mock_sensor_id):
    """Weekly view of a fully seeded week returns one aggregate per weekday."""

    data = _get(client, user_headers, mock_sensor_id, "weekly", datetime.now() - timedelta(days=7))

    assert data["timeframe"] == "weekly"
    assert len(data["data"]) == 7
    _assert_consistent(data["data"])


def test_get_temperature_monthly(client, user_headers, mock_sensor_id):
    """Monthly view of a fully seeded month returns one aggregate per day."""

    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    data = _get(client, user_headers, mock_sensor_id, "monthly", last_month)

    assert data["timeframe"] == "monthly"
    assert len(data["data"]) == calendar.monthrange(last_month.year, last_month.month)[1]
    _assert_consistent(data["data"])


def test_get_temperature_yearly(client, user_headers, mock_sensor_id):
    """Yearly view of a fully seeded year returns one aggregate per month."""

    data = _get(client, user_headers, mock_sensor_id, "yearly", datetime.now() - timedelta(days=365))
    # ~400 days of history always fully cover the previous calendar year's
    # months from the oldest seeded month up to December.

    assert data["timeframe"] == "yearly"
    assert 1 <= len(data["data"]) <= 12
    _assert_consistent(data["data"])


def test_get_temperature_outside_mock_history_is_empty(client, user_headers, mock_sensor_id):
    """Dates older than the mocked history have no readings."""

    data = _get(client, user_headers, mock_sensor_id, "daily", datetime.now() - timedelta(days=800))

    assert data["data"] == []


@pytest.mark.parametrize("sensor_index", [0, 1, 2])
def test_get_temperature_for_each_mock_sensor(client, user_headers, mock_sensor_ids, sensor_index):
    """Every sensor created by the mock data script serves data."""

    sensor_id = mock_sensor_ids[sensor_index]
    data = _get(client, user_headers, sensor_id, "daily", datetime.now() - timedelta(days=1))

    assert data["sensor_id"] == sensor_id
    assert len(data["data"]) == 24


def test_get_temperature_unknown_sensor_is_empty(client, user_headers):
    """A sensor without readings yields an empty data set rather than an error."""

    data = _get(client, user_headers, "does-not-exist", "daily", datetime.now() - timedelta(days=1))

    assert data["data"] == []


def test_mock_readings_have_fine_resolution_for_recent_days(app, mock_sensor_id):
    """The last 14 days are seeded every 10 minutes, i.e. 144 readings per day."""

    day_start = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    count = TemperatureReading.query.filter(
        TemperatureReading.sensor_id == mock_sensor_id,
        TemperatureReading.timestamp >= day_start,
        TemperatureReading.timestamp < day_start + timedelta(days=1),
    ).count()

    assert count == 144


def test_get_sensors(client, user_headers, mock_sensor_ids):
    """The sensors endpoint lists every sensor with mocked readings."""

    response = client.get("/api/sensors", headers=user_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "sensors" in data
    for sensor_id in mock_sensor_ids:
        assert sensor_id in data["sensors"]


def test_zero_degree_readings_are_not_reported_as_missing(client, admin_headers, db_session):
    """0 degree Celsius is a valid reading and must not be turned into null."""

    day = datetime.now() - timedelta(days=3)
    db_session.add(TemperatureReading(sensor_id="zero-sensor", temperature=0.0, humidity=0.0, timestamp=day))
    db_session.commit()

    data = _get(client, admin_headers, "zero-sensor", "daily", day)

    assert data["data"][0]["avg_temperature"] == 0.0
    assert data["data"][0]["min_temperature"] == 0.0
    assert data["data"][0]["max_temperature"] == 0.0
