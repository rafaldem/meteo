import time
import pytest
import threading


def test_login_performance(client):
    """Test login endpoint performance."""

    start_time = time.time()

    response = client.post("/auth/login", json={"username": "admin", "password": "admin_password"})

    end_time = time.time()
    duration = end_time - start_time

    assert response.status_code == 200
    assert duration < 0.5


@pytest.mark.parametrize("timeframe", ["daily", "weekly", "monthly", "yearly"])
def test_temperature_query_performance(client, admin_headers, mock_sensor_id, timeframe):
    """Test temperature query performance against the mocked data set.

    The mock data script seeds ~400 days of history per sensor (over 11k
    readings), which is a realistic dataset size for the aggregate queries.
    """

    start_time = time.time()

    response = client.get(f"/api/temperature/{mock_sensor_id}?timeframe={timeframe}", headers=admin_headers)

    end_time = time.time()
    duration = end_time - start_time

    assert response.status_code == 200
    assert duration < 1.0  # Query should take less than 1 second


def test_concurrent_requests(client, admin_headers):
    """Test handling multiple concurrent requests."""

    def make_request(thread_results, index):
        response = client.get("/api/sensors", headers=admin_headers)
        thread_results[index] = response.status_code

    results = [0] * 10
    threads = []

    start_time = time.time()

    for i in range(10):
        thread = threading.Thread(target=make_request, args=(results, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    duration = end_time - start_time

    assert all(code == 200 for code in results)
    assert duration < 2.0  # All requests should complete in less than 2 seconds


def test_database_performance(client, admin_headers, db_session):
    """Test database write performance."""

    readings = []
    for i in range(100):
        readings.append(
            {"sensor_id": f"perf-sensor-{i % 10}", "temperature": 20.0 + (i % 10), "humidity": 50.0 + (i % 20)}
        )

    start_time = time.time()

    for reading in readings:
        response = client.post("/api/temperature", headers=admin_headers, json=reading)
        assert response.status_code == 201

    end_time = time.time()
    duration = end_time - start_time

    assert duration < 10.0  # Should take less than 10 seconds total (100ms per request)
