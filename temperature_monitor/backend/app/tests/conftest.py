from datetime import datetime, timedelta
from pathlib import Path

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


@pytest.fixture(scope="session")
def sample_app_settings():
    """Sample app settings for testing"""
    return {
        "TITLE": "Test title",
        "DESCRIPTION": "Test description",
        "VERSION": "0.1.0",
        "AUTHOR": {
            "name": "Test Author",
            "email": "test@example.com",
        },
    }


@pytest.fixture(scope="session")
def app(sample_app_settings):
    """Create a Flask app context for the tests."""
    TestConfig.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    app = create_app(TestConfig, sample_app_settings)

    # Establish an application context before running the tests
    with app.app_context():
        db.create_all()
        _init_test_data()
        yield app
        db.session.remove()
        db.drop_all()


def _init_test_data():
    """Initialize test data."""
    # Create test users
    admin_user = User(username="admin", email="admin@example.com", is_admin=True)
    admin_user.set_password("admin-password")

    regular_user = User(username="user", email="user@example.com", is_admin=False)
    regular_user.set_password("user-password")

    db.session.add(admin_user)
    db.session.add(regular_user)

    sensor1 = Sensor(
        id="test-sensor-1",
        name="Test Sensor 1",
        sensor_id="s001",
        location="Test Location",
        description="Temperature sensor for test location 1",
    )

    sensor2 = Sensor(
        id="test-sensor-2",
        name="Test Sensor 2",
        sensor_id="s002",
        location="Another Location",
        description="Temperature sensor for test location 2",
    )
    db.session.add(sensor1)
    db.session.add(sensor2)

    # Create some temperature readings for the past 7 days
    now = datetime.now()
    for day in range(7):
        # Add readings for multiple times in a day
        timestamp = now - timedelta(days=day)

        for hour in [8, 12, 16, 20]:
            reading_time = timestamp.replace(hour=hour, minute=0, second=0)
            reading1 = TemperatureReading(
                sensor_id="test-sensor-1",
                temperature=20 + day + (hour / 10),
                timestamp=reading_time,  # Varying temperature
            )
            reading2 = TemperatureReading(
                sensor_id="test-sensor-2", temperature=18 + day + (hour / 10), timestamp=reading_time
            )
            db.session.add(reading1)
            db.session.add(reading2)

    # Create some app settings
    settings = [
        AppSettings(key="SITE_TITLE", value="Temperature Monitor", description="Site title", requires_admin=True),
        AppSettings(key="ALERT_THRESHOLD", value="30", description="Temperature alert threshold", requires_admin=True),
        AppSettings(
            key="ALERT_RECIPIENTS", value="admin@example.com", description="Alert recipients", requires_admin=True
        ),
        AppSettings(key="DISPLAY_UNITS", value="C", description="Display units (C/F)", requires_admin=False),
    ]

    for setting in settings:
        db.session.add(setting)

    db.session.commit()


@pytest.fixture(scope="session")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="session")
def db_session(app):
    """Creates a new database session for each test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    # Use a nested transaction for test isolation
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    # Patch the session on the db instance
    db.session = session

    yield session

    # Cleanup
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture(scope="session")
def admin_token():
    """Create a JWT token for admin authentication."""

    # Make sure you're creating a token with the proper subject field
    return create_access_token(
        identity={"username": "admin", "user_id": 1},  # Make sure this contains a string subject
        expires_delta=timedelta(hours=1),
        additional_claims={"is_admin": True},
    )


@pytest.fixture(scope="session")
def user_token(app):
    """JWT token for regular user."""
    with app.app_context():
        user = User.query.filter_by(username="user").first()
        expires = timedelta(hours=1)
        access_token = create_access_token(
            identity=user.id, additional_claims={"is_admin": False}, expires_delta=expires
        )
        return access_token


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    """Headers with admin JWT token."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def user_headers(user_token):
    """Headers with user JWT token."""
    return {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }
