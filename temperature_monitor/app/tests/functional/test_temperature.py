import json

from app.models import TemperatureReading


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

    # Verify in database
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

    # Should fail because only admins can add temperatures
    assert response.status_code == 403
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Admin privileges required"


def test_get_temperature_daily(client, user_headers):
    """Test getting daily temperature data."""
    response = client.get("/api/temperature/test-sensor-1?timeframe=daily", headers=user_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["sensor_id"] == "test-sensor-1"
    assert data["timeframe"] == "daily"
    assert "data" in data
    assert len(data["data"]) > 0

    # Check data structure
    first_entry = data["data"][0]
    assert "time_group" in first_entry
    assert "avg_temperature" in first_entry
    assert "min_temperature" in first_entry
    assert "max_temperature" in first_entry
    assert "avg_humidity" in first_entry


def test_get_temperature_weekly(client, user_headers):
    """Test getting weekly temperature data."""
    response = client.get("/api/temperature/test-sensor-1?timeframe=weekly", headers=user_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["timeframe"] == "weekly"


def test_get_temperature_monthly(client, user_headers):
    """Test getting monthly temperature data."""
    response = client.get("/api/temperature/test-sensor-1?timeframe=monthly", headers=user_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["timeframe"] == "monthly"


def test_get_temperature_yearly(client, user_headers):
    """Test getting yearly temperature data."""
    response = client.get("/api/temperature/test-sensor-1?timeframe=yearly", headers=user_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["timeframe"] == "yearly"


def test_get_sensors(client, user_headers):
    """Test getting list of sensors."""
    response = client.get("/api/sensors", headers=user_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "sensors" in data
    assert "test-sensor-1" in data["sensors"]
    assert "test-sensor-2" in data["sensors"]
