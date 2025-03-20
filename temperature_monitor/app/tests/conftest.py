import os
import tempfile
from datetime import datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token

from app import create_app, db, bcrypt
from app.models import User, UserRole, TemperatureReading, AppSettings


@pytest.fixture(scope='function')
def app():
   """Create and configure a Flask app for testing."""
   # Create a temporary file to isolate the database for each test
   db_fd, db_path = tempfile.mkstemp()

   app = create_app({
      'TESTING': True,
      'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
      'SQLALCHEMY_TRACK_MODIFICATIONS': False,
      'JWT_SECRET_KEY': 'test-secret-key',
      'SECRET_KEY': 'test-secret-key',
   })

   # Create the database and load test data
   with app.app_context():
      db.create_all()
      _init_test_data()

   yield app

   # Close and remove the temporary database
   os.close(db_fd)
   os.unlink(db_path)

def _init_test_data():
   """Initialize test data in the database."""
   # Create test users
   admin_password = bcrypt.generate_password_hash('admin_password').decode('utf-8')
   user_password = bcrypt.generate_password_hash('user_password').decode('utf-8')

   admin_user = User(
      username='admin',
      email='admin@example.com',
      password_hash=admin_password,
      role=UserRole.ADMIN
   )

   regular_user = User(
      username='user',
      email='user@example.com',
      password_hash=user_password,
      role=UserRole.USER
   )

   db.session.add(admin_user)
   db.session.add(regular_user)

   # Create sample temperature readings
   base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
   for i in range(24):  # 24 hours of data
      reading_time = base_date + timedelta(hours=i)
      reading = TemperatureReading(
         sensor_id='test-sensor-1',
         temperature=20.0 + (i % 10),  # Fluctuating temperature
         humidity=50.0 + (i % 20),     # Fluctuating humidity
         timestamp=reading_time
      )
      db.session.add(reading)

   # Add a second sensor with data
   for i in range(24):
      reading_time = base_date + timedelta(hours=i)
      reading = TemperatureReading(
         sensor_id='test-sensor-2',
         temperature=18.0 + (i % 8),
         humidity=45.0 + (i % 15),
         timestamp=reading_time
      )
      db.session.add(reading)

   # Create some app settings
   db.session.add(AppSettings(key='sampling_rate', value='300', description='Sensor sampling rate in seconds', requires_admin=True))
   db.session.add(AppSettings(key='display_units', value='celsius', description='Temperature display units', requires_admin=False))

   db.session.commit()

@pytest.fixture(scope='function')
def client(app):
   """A test client for the app."""
   return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
   """A database session for the tests."""
   with app.app_context():
      connection = db.engine.connect()
      transaction = connection.begin()

      session = db.session

      yield session

      session.close()
      transaction.rollback()
      connection.close()

@pytest.fixture(scope='function')
def admin_token(app):
   """JWT token for admin user."""
   with app.app_context():
      admin = User.query.filter_by(username='admin').first()
      token = create_access_token(identity=admin.id)
      return token

@pytest.fixture(scope='function')
def user_token(app):
   """JWT token for regular user."""
   with app.app_context():
      user = User.query.filter_by(username='user').first()
      token = create_access_token(identity=user.id)
      return token

@pytest.fixture(scope='function')
def admin_headers(admin_token):
   """Headers with admin JWT token."""
   return {'Authorization': f'Bearer {admin_token}'}

@pytest.fixture(scope='function')
def user_headers(user_token):
   """Headers with user JWT token."""
   return {'Authorization': f'Bearer {user_token}'}
