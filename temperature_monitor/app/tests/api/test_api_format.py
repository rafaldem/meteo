import json

import pytest


def test_api_response_format(client, admin_headers):
    """Test that API responses follow a consistent format."""
    endpoints = [
        ("/auth/profile", "GET"),
        ("/api/sensors", "GET"),
        ("/api/temperature/test-sensor-1?timeframe=daily", "GET"),
        ("/admin/settings", "GET"),
    ]

    for endpoint, method in endpoints:
        if method == "GET":
            response = client.get(endpoint, headers=admin_headers)
        else:
            continue  # Add POST, PUT handlers if needed

        assert response.status_code == 200
        assert response.content_type == "application/json"

        # Ensure we can parse the JSON response
        try:
            data = json.loads(response.data)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail(f"Response for {endpoint} is not valid JSON")

        # For successful responses, there should be no 'error' key
        assert "error" not in data


def test_api_error_format(client, admin_headers):
    """Test that API error responses follow a consistent format."""
    # Test with non-existent endpoint
    response = client.get("/api/nonexistent", headers=admin_headers)
    assert response.status_code in [404, 405]

    # Test with missing required field
    response = client.post(
        "/auth/register",
        json={
            "username": "incomplete",
            # Missing email and password
        },
    )

    assert response.status_code == 400
    try:
        data = json.loads(response.data)
        assert "error" in data
        assert isinstance(data["error"], str)
    except json.JSONDecodeError:
        pytest.fail("Error response is not valid JSON")
