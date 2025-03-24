import os
import tempfile
from datetime import datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token

from app import create_app, db, bcrypt
from app.models import User, UserRole, TemperatureReading, AppSettings, Sensor


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-secret-key"
    SECRET_KEY = "test-secret-key"


@pytest.fixture
def sample_app_settings():
    """Fixture to provide a sample AppSettings object."""
    return AppSettings(
        id=1,
        key="sample_key",
        value="sample_value",
        description="Sample description",
        requires_admin=True
    )


@pytest.fixture(scope="function")
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()

    # Create a TestConfig instance and set the database URI
    test_config = TestConfig()
    test_config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    app = create_app(test_config)

    # Create the database and load test data
    with app.app_context():
        db.create_all()
        _init_test_data()

    yield app

    # Close and remove the temporary database
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except (IOError, PermissionError) as e:
        print(f"Error closing and removing the temporary database: {e}")


def _init_test_data():
    """Initialize test data in the database."""
    # Create test users
    admin_password = bcrypt.generate_password_hash("admin_password").decode("utf-8")
    user_password = bcrypt.generate_password_hash("user_password").decode("utf-8")

    admin_user = User(username="admin", email="admin@example.com", password_hash=admin_password, role=UserRole.ADMIN)

    regular_user = User(username="user", email="user@example.com", password_hash=user_password, role=UserRole.USER)

    db.session.add(admin_user)
    db.session.add(regular_user)

    # Create test sensors - ensure test-sensor-1 exists
    sensor1 = Sensor(id="test-sensor-1", name="Test Sensor 1", location="Test Location")
    sensor2 = Sensor(id="test-sensor-2", name="Test Sensor 2", location="Another Location")

    db.session.add(sensor1)
    db.session.add(sensor2)

    # Add temperature readings for the past week to support daily timeframe
    now = datetime.now()
    for day in range(7):
        timestamp = now - timedelta(days=day)
        # Add multiple readings per day
        for hour in [8, 12, 16, 20]:
            reading_time = timestamp.replace(hour=hour, minute=0, second=0)
            reading1 = TemperatureReading(
                sensor_id="test-sensor-1", temperature=20 + day + (hour / 10), timestamp=reading_time  # Varying temperature
            )
            reading2 = TemperatureReading(
                sensor_id="test-sensor-2", temperature=18 + day + (hour / 10), timestamp=reading_time
            )
            db.session.add(reading1)
            db.session.add(reading2)

    # Create some app settings
    db.session.add(
        AppSettings(
            key="sampling_rate", value="300", description="Sensor sampling rate in seconds", requires_admin=True
        )
    )
    db.session.add(
        AppSettings(key="display_units", value="celsius", description="Temperature display units", requires_admin=False)
    )

    db.session.commit()


@pytest.fixture(scope="function")
def client(app):
    """A test client for the app."""
    app.testing = True
    return app.test_client()


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def admin_token(app):
    """JWT token for admin user."""
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        expires = timedelta(hours=1)
        access_token = create_access_token(
            identity=admin.id, additional_claims={"is_admin": True}, expires_delta=expires
        )
        return access_token


@pytest.fixture(scope="function")
def user_token(app):
    """JWT token for regular user."""
    with app.app_context():
        user = User.query.filter_by(username="user").first()
        token = create_access_token(identity=user.id)
        return token


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    """Headers with admin JWT token."""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="function")
def user_headers(user_token):
    """Headers with user JWT token."""
    return {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
