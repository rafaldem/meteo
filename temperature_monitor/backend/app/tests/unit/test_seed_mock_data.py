"""Tests for the mock data script itself and the data it leaves in the test DB."""

import random
from datetime import datetime, timedelta

from app import db
from models import Sensor, TemperatureReading
from utils.seed_mock_data import MOCK_SENSORS, generate_readings, seed_mock_data


def test_mock_sensors_are_registered(app, mock_sensor_ids):
    """The seeder registers each mock sensor in the sensors table."""
    registered = {sensor.id for sensor in Sensor.query.all()}

    assert set(mock_sensor_ids) <= registered


def test_mock_history_covers_about_a_year(app, mock_sensor_id):
    """Yearly charts need ~400 days of history."""
    oldest = db.session.query(db.func.min(TemperatureReading.timestamp)).filter_by(sensor_id=mock_sensor_id).scalar()
    newest = db.session.query(db.func.max(TemperatureReading.timestamp)).filter_by(sensor_id=mock_sensor_id).scalar()

    assert datetime.now() - oldest >= timedelta(days=399)
    assert datetime.now() - newest <= timedelta(minutes=20)


def test_seeding_is_idempotent(app, mock_sensor_id):
    """Running the seeder again without --refresh must not duplicate readings."""
    before = TemperatureReading.query.filter_by(sensor_id=mock_sensor_id).count()

    assert seed_mock_data() == 0
    assert TemperatureReading.query.filter_by(sensor_id=mock_sensor_id).count() == before


def test_generation_is_deterministic():
    """The same seed produces the same readings (what keeps test data stable)."""
    sensor = MOCK_SENSORS[0]
    start = datetime(2025, 1, 1)
    end = start + timedelta(days=2)

    def readings():
        rng = random.Random(f"42:{sensor['id']}")
        return list(generate_readings(sensor, start, end, end - timedelta(days=1), 10, 60, rng))

    assert readings() == readings()
