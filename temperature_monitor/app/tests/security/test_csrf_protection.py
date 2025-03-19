def test_csrf_protection(client):
    """Test CSRF protection for API endpoints."""
    # Flask-JWT-Extended provides CSRF protection for cookies
    # We're using token-based auth without cookies, but we should still verify
    # that non-GET requests require proper authentication

    # Try to update profile without token
    response = client.put("/auth/profile", json={"email": "csrf_test@example.com"})

    assert response.status_code in [401, 403]  # Either unauthorized or forbidden
