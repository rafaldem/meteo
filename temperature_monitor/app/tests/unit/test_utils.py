from unittest.mock import patch, MagicMock

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

from app.models import UserRole
from app.utils.decorators import admin_required


@pytest.fixture
def jwt_authenticated_app():
    """
    Creates a Flask application with JWT authentication configured.

    This fixture is necessary for testing functions that use JWT authentication,
    such as the admin_required decorator which verifies JWT identity claims.
    The JWT manager must be initialized for these tests to work properly.
    """
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-key"
    # Initialize JWTManager without storing the reference
    JWTManager(app)
    return app


def test_admin_required_decorator(jwt_authenticated_app):
    """Test the admin_required decorator."""
    with jwt_authenticated_app.app_context():
        # Mock the get_jwt_identity function
        with patch("app.utils.decorators.get_jwt_identity", return_value=1):
            # Mock the User.query
            with patch("app.utils.decorators.User") as MockUser:
                # Set up the mock user
                mock_user = MagicMock()
                MockUser.query.get.return_value = mock_user

                # Test with admin user
                mock_user.role = UserRole.ADMIN

                @admin_required
                def admin_function():
                    return "Admin access granted"

                result = admin_function()
                assert result == "Admin access granted"

                # Test with regular user
                mock_user.role = UserRole.USER
                with pytest.raises(Exception):
                    admin_function()
