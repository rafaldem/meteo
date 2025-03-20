import json

from flask_jwt_extended import decode_token


def test_password_security(client):
    """Test that passwords are properly hashed and not stored in plaintext."""
    # Register a new user
    client.post(
        "/auth/register",
        json={"username": "security_test", "email": "security@example.com", "password": "test_password"},
    )

    # Login to verify the account was created
    client.post("/auth/login", json={"username": "security_test", "password": "test_password"})

    # Attempt to get the user's stored password from the database
    with client.application.app_context():
        from app.models import User

        user = User.query.filter_by(username="security_test").first()

        # Ensure password is not stored in plaintext
        assert user.password_hash != "test_password"

        # Verify we can't reverse the hash
        assert "test_password" not in user.password_hash


def test_token_expiration(client, app):
    """Test that JWT tokens expire after the configured time."""
    # Login to get a token
    response = client.post("/auth/login", json={"username": "admin", "password": "admin_password"})

    data = json.loads(response.data)
    token = data["access_token"]

    # Verify token expiration time
    with app.app_context():
        decoded = decode_token(token)
        exp = decoded["exp"]
        iat = decoded["iat"]

        # Token should expire in about 1 hour
        assert (exp - iat) == 3600  # 1 hour = 3600 seconds


def test_token_refresh(client):
    """Test token refresh mechanism."""
    # Login to get tokens
    response = client.post("/auth/login", json={"username": "admin", "password": "admin_password"})

    data = json.loads(response.data)
    refresh_token = data["refresh_token"]

    # Refresh to get a new access token
    response = client.post("/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "access_token" in data


def test_authorization_boundaries(client, user_headers, admin_headers):
    """Test that authorization boundaries are enforced."""
    # Test admin endpoint with regular user
    response = client.get("/admin/users", headers=user_headers)
    assert response.status_code == 403

    # Test admin endpoint with admin user
    response = client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200

    # Test regular user endpoint with both users
    response1 = client.get("/api/sensors", headers=user_headers)
    response2 = client.get("/api/sensors", headers=admin_headers)
    assert response1.status_code == 200
    assert response2.status_code == 200


def test_token_tampering(client, admin_token):
    """Test that tampered tokens are rejected."""
    # Tamper with the token
    tampered_token = admin_token[:-5] + "XXXXX"

    response = client.get("/auth/profile", headers={"Authorization": f"Bearer {tampered_token}"})

    assert response.status_code in [401, 422]  # Either unauthorized or unprocessable entity
