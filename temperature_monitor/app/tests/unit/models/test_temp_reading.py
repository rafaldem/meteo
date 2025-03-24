from datetime import datetime

from models import TemperatureReading


def test_temperature_reading_creation(self, db_session):
    """Test creating a temperature reading."""
    reading = TemperatureReading(
        sensor_id="test-sensor", temperature=25.5, humidity=60.0, timestamp=datetime.now()
    )
    db_session.add(reading)
    db_session.commit()

    retrieved_reading = TemperatureReading.query.filter_by(sensor_id="test-sensor").first()
    assert retrieved_reading is not None
    assert retrieved_reading.temperature == 25.5
    assert retrieved_reading.humidity == 60.0

def test_temperature_reading_to_dict(self, db_session):
    """Test the to_dict method of the TemperatureReading model."""
    reading = TemperatureReading.query.first()
    reading_dict = reading.to_dict()

    assert "id" in reading_dict
    assert "sensor_id" in reading_dict
    assert "temperature" in reading_dict
    assert "humidity" in reading_dict
    assert "timestamp" in reading_dict
