import pytest

from flask_jwt_extended import create_access_token
from datetime import timedelta
from app import create_app, db, bcrypt
from models import User, UserRole, AppSettings
from utils.seed_mock_data import MOCK_SENSORS, seed_mock_data


MOCK_DATA_SEED = 42


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
def app(sample_app_settings, tmp_path_factory):
    """Create a Flask app context for the tests.

    A file-based SQLite DB is used instead of ``:memory:`` because in-memory
    SQLite is served through a single shared connection, which breaks the
    concurrent-request tests once the DB holds the (large) mocked data set.
    """

    db_file = tmp_path_factory.mktemp("db") / "test.db"
    TestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file}"
    app = create_app(TestConfig, sample_app_settings)

    with app.app_context():
        db.create_all()
        _init_test_data()
        yield app
        db.session.remove()
        db.drop_all()


def _init_test_data():
    """Initialize test data."""

    admin_user = User(
        username="admin",
        email="admin@example.com",
        role=UserRole.ADMIN,
        password_hash=bcrypt.generate_password_hash("admin_password").decode("utf-8"),
    )

    regular_user = User(
        username="user",
        email="user@example.com",
        role=UserRole.USER,
        password_hash=bcrypt.generate_password_hash("user_password").decode("utf-8"),
    )

    db.session.add(admin_user)
    db.session.add(regular_user)

    db.session.commit()

    # Sensors and readings come from the same generator used to seed real
    # deployments (utils/seed_mock_data.py). The default seed is fixed, so the
    # data set is deterministic; timestamps are relative to "now", so the
    # last 14 days are fine-grained and the rest of the ~400 days is hourly.
    seed_mock_data(seed=MOCK_DATA_SEED)

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


@pytest.fixture(autouse=True)
def _clean_session(app):
    """Roll back after every test so a failed flush cannot break later tests."""

    yield
    db.session.rollback()


@pytest.fixture(scope="session")
def mock_sensors():
    """Definitions of the sensors created by the mock data script."""

    return MOCK_SENSORS


@pytest.fixture(scope="session")
def mock_sensor_ids(mock_sensors):
    """IDs of the sensors that have mocked readings in the test database."""

    return [sensor["id"] for sensor in mock_sensors]


@pytest.fixture(scope="session")
def mock_sensor_id(mock_sensor_ids):
    """ID of the main mocked sensor (outdoor, full seasonal range)."""

    return mock_sensor_ids[0]


@pytest.fixture(scope="session")
def client(app):
    """A test client for the app."""

    return app.test_client()


@pytest.fixture(scope="session")
def db_session(app):
    """The app's SQLAlchemy session (app context is held open by the `app` fixture)."""

    yield db.session
    db.session.rollback()


@pytest.fixture(scope="session")
def admin_token(app):
    """JWT token for the seeded admin user."""

    user = User.query.filter_by(username="admin").first()
    return create_access_token(
        identity=str(user.id),
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
            identity=str(user.id), additional_claims={"is_admin": False}, expires_delta=expires
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
