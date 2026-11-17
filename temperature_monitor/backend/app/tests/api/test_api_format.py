import json
import pytest

from utils.seed_mock_data import MOCK_SENSORS


MOCK_SENSOR_ID = MOCK_SENSORS[0]["id"]


@pytest.mark.parametrize(
    "endpoint,method",
    [
        ("/auth/profile", "GET"),
        ("/api/sensors", "GET"),
        (f"/api/temperature/{MOCK_SENSOR_ID}?timeframe=daily", "GET"),
        ("/admin/settings", "GET"),
    ],
)
def test_individual_endpoints(client, admin_headers, endpoint, method):
    """Test that each API endpoint returns a successful response."""

    if method == "GET":
        response = client.get(endpoint, headers=admin_headers)

        print(f"Testing {endpoint}: Status={response.status_code}, Data={response.data[:100]}")

        if response.status_code != 200:
            print(f"ERROR: Endpoint {endpoint} failed with status {response.status_code} and response {response.data}")

        assert response.status_code == 200
        assert response.content_type == "application/json"

        try:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            assert "error" not in data

        except json.JSONDecodeError:
            pytest.fail(f"Response for {endpoint} is not valid JSON")

    else:
        pytest.skip(f"Test for {method} method not implemented")


def test_api_error_format(client, admin_headers):
    """Test that API error responses follow a consistent format."""

    response = client.get("/api/nonexistent", headers=admin_headers)
    assert response.status_code in [404, 405]

    response = client.post(
        "/auth/register",
        json={
            "username": "incomplete",
        },
    )

    assert response.status_code == 400
    try:
        data = json.loads(response.data)
        assert "error" in data
        assert isinstance(data["error"], str)
    except json.JSONDecodeError:
        pytest.fail("Error response is not valid JSON")
