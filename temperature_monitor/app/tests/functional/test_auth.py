import json

from app.models import User, UserRole


def test_register(client, db_session):
    """Test user registration."""
    response = client.post(
        "/auth/register", json={"username": "newuser", "email": "newuser@example.com", "password": "password123"}
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "User registered successfully"

    # Verify user was created in the database
    user = User.query.filter_by(username="newuser").first()
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.role == UserRole.USER  # Since admin already exists


def test_register_duplicate_username(client):
    """Test registration with duplicate username."""
    response = client.post(
        "/auth/register",
        json={"username": "admin", "email": "different@example.com", "password": "password123"},  # Already exists
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Username already exists"


def test_login_success(client):
    """Test successful login."""
    response = client.post("/auth/login", json={"username": "admin", "password": "admin_password"})

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong_password"})

    assert response.status_code == 401
    data = json.loads(response.data)
    assert "error" in data
    assert data["error"] == "Invalid username or password"


def test_profile_get(client, admin_headers):
    """Test getting user profile."""
    response = client.get("/auth/profile", headers=admin_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["username"] == "admin"
    assert data["email"] == "admin@example.com"
    assert data["role"] == "admin"


def test_profile_update(client, admin_headers, db_session):
    """Test updating user profile."""
    response = client.put(
        "/auth/profile", headers=admin_headers, json={"email": "updated@example.com", "theme": "dark"}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["email"] == "updated@example.com"
    assert data["theme"] == "dark"

    # Verify changes in database
    user = User.query.filter_by(username="admin").first()
    assert user.email == "updated@example.com"
    assert user.theme == "dark"
