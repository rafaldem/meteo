import pytest
from app.models import User, UserRole, TemperatureReading, AppSettings
from datetime import datetime

class TestUserModel:
   def test_user_creation(self, db_session):
      """Test creating a user."""
      user = User(
         username='testuser',
         email='test@example.com',
         password_hash='hashed_password',
         role=UserRole.USER
      )
      db_session.add(user)
      db_session.commit()

      retrieved_user = User.query.filter_by(username='testuser').first()
      assert retrieved_user is not None
      assert retrieved_user.email == 'test@example.com'
      assert retrieved_user.password_hash == 'hashed_password'
      assert retrieved_user.role == UserRole.USER

   def test_user_to_dict(self, db_session):
      """Test the to_dict method of the User model."""
      user = User.query.filter_by(username='admin').first()
      user_dict = user.to_dict()

      assert user_dict['username'] == 'admin'
      assert user_dict['email'] == 'admin@example.com'
      assert user_dict['role'] == 'admin'
      assert 'password_hash' not in user_dict  # Ensure password hash is not exposed
      assert 'theme' in user_dict
      assert 'dashboard_layout' in user_dict

class TestTemperatureReadingModel:
   def test_temperature_reading_creation(self, db_session):
      """Test creating a temperature reading."""
      reading = TemperatureReading(
         sensor_id='test-sensor',
         temperature=25.5,
         humidity=60.0,
         timestamp=datetime.utcnow()
      )
      db_session.add(reading)
      db_session.commit()

      retrieved_reading = TemperatureReading.query.filter_by(sensor_id='test-sensor').first()
      assert retrieved_reading is not None
      assert retrieved_reading.temperature == 25.5
      assert retrieved_reading.humidity == 60.0

   def test_temperature_reading_to_dict(self, db_session):
      """Test the to_dict method of the TemperatureReading model."""
      reading = TemperatureReading.query.first()
      reading_dict = reading.to_dict()

      assert 'id' in reading_dict
      assert 'sensor_id' in reading_dict
      assert 'temperature' in reading_dict
      assert 'humidity' in reading_dict
      assert 'timestamp' in reading_dict

class TestAppSettingsModel:
   def test_app_settings_creation(self, db_session):
      """Test creating an app setting."""
      setting = AppSettings(
         key='test_setting',
         value='test_value',
         description='A test setting',
         requires_admin=True
      )
      db_session.add(setting)
      db_session.commit()

      retrieved_setting = AppSettings.query.filter_by(key='test_setting').first()
      assert retrieved_setting is not None
      assert retrieved_setting.value == 'test_value'
      assert retrieved_setting.description == 'A test setting'
      assert retrieved_setting.requires_admin is True
