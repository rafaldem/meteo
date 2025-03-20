import time
from datetime import datetime


def test_login_performance(client):
    """Test login endpoint performance."""
    start_time = time.time()

    response = client.post("/auth/login", json={"username": "admin", "password": "admin_password"})

    end_time = time.time()
    duration = end_time - start_time

    assert response.status_code == 200
    assert duration < 0.5  # Login should take less than 500ms


def test_temperature_query_performance(client, admin_headers, db_session):
    """Test temperature query performance with larger dataset."""
    # First, add more data to the database
    with client.application.app_context():
        from app.models import TemperatureReading

        # Add 1000 temperature readings
        base_date = datetime.now()
        readings = []
        for i in range(1000):
            reading = TemperatureReading(
                sensor_id="perf-test-sensor", temperature=20.0 + (i % 10), humidity=50.0 + (i % 20), timestamp=base_date
            )
            readings.append(reading)

        db_session.bulk_save_objects(readings)
        db_session.commit()

    # Now test query performance
    start_time = time.time()

    response = client.get("/api/temperature/perf-test-sensor?timeframe=daily", headers=admin_headers)

    end_time = time.time()
    duration = end_time - start_time

    assert response.status_code == 200
    assert duration < 1.0  # Query should take less than 1 second


def test_concurrent_requests(client, admin_headers):
    """Test handling multiple concurrent requests."""
    import threading

    # Define a function to make requests
    def make_request(thread_results, index):
        response = client.get("/api/sensors", headers=admin_headers)
        thread_results[index] = response.status_code

    # Make 10 concurrent requests
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

    # All requests should succeed
    assert all(code == 200 for code in results)

    # Should handle all requests quickly
    assert duration < 2.0  # All requests should complete in less than 2 seconds


def test_database_performance(client, admin_headers, db_session):
    """Test database write performance."""
    # Time how long it takes to add 100 temperature readings
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

    # Adding 100 readings should be reasonably fast
    assert duration < 10.0  # Should take less than 10 seconds total (100ms per request)
