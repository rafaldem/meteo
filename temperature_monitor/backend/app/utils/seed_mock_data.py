#!/usr/bin/env python3

"""
Seed the database with mocked, realistic historical temperature data.

Covers enough history for every chart in the dashboard:
  * daily   -> fine-grained readings (default every 10 min) for the last 14 days
  * weekly  -> same fine-grained window (7+ days)
  * monthly -> hourly readings
  * yearly  -> hourly readings going back ~400 days

Only the mock sensors defined below are ever touched, so real sensor data is
never modified. Timestamps are relative to now, so re-running with --refresh
shifts the whole window forward.

Usage (from backend/app):
    python seed_mock_data.py                 # seed if mock sensors have no data
    python seed_mock_data.py --refresh       # wipe + regenerate mock sensors only
    python seed_mock_data.py --days 730 --seed 7
"""


import argparse
import math
import os
import random
import sys
from datetime import datetime, timedelta

from app import db
from models import Sensor, TemperatureReading


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Climate parameters (mean ~9 C, +/-10 C over the year)
ANNUAL_MEAN = 9.0
ANNUAL_AMPLITUDE = 10.0
COLDEST_DAY_OF_YEAR = 15
WEATHER_SIGMA = 3.5  # std-dev of multi-day weather swings (C)
WEATHER_MEMORY_HOURS = 48.0  # how long a warm/cold spell tends to persist


MOCK_SENSORS = [
    {
        "id": "mock-outdoor",
        "name": "Mock Outdoor",
        "sensor_id": "mock-001",
        "location": "Garden",
        "description": "Mocked outdoor sensor (generated data)",
        "bias": 0.0, "seasonal_scale": 1.0, "diurnal_scale": 1.0, "weather_scale": 1.0, "noise": 0.15,
    },
    {
        "id": "mock-garage",
        "name": "Mock Garage",
        "sensor_id": "mock-002",
        "location": "Garage",
        "description": "Mocked semi-sheltered sensor (generated data)",
        "bias": 1.5, "seasonal_scale": 0.8, "diurnal_scale": 0.5, "weather_scale": 0.6, "noise": 0.1,
    },
    {
        "id": "mock-indoor",
        "name": "Mock Indoor",
        "sensor_id": "mock-003",
        "location": "Living room",
        "description": "Mocked indoor sensor (generated data)",
        "bias": 12.0, "seasonal_scale": 0.15, "diurnal_scale": 0.15, "weather_scale": 0.1, "noise": 0.05,
    },
]


def _seasonal(ts):
    """Annual cycle: coldest mid-January, warmest mid-July."""
    doy = ts.timetuple().tm_yday + ts.hour / 24
    return ANNUAL_MEAN - ANNUAL_AMPLITUDE * math.cos(2 * math.pi * (doy - COLDEST_DAY_OF_YEAR) / 365.25)


def _diurnal(ts, seasonal):
    """Daily cycle: min ~03:00, max ~15:00; swing is larger in summer."""
    summer = (seasonal - (ANNUAL_MEAN - ANNUAL_AMPLITUDE)) / (2 * ANNUAL_AMPLITUDE)
    amplitude = 2.0 + 3.5 * summer
    hour = ts.hour + ts.minute / 60
    return -amplitude * math.cos(2 * math.pi * (hour - 3) / 24)


def generate_readings(sensor, start, end, fine_from, fine_step_min, coarse_step_min, rng):
    """Yield reading dicts in chronological order for one sensor."""
    weather = rng.gauss(0, WEATHER_SIGMA)
    ts = start
    while ts <= end:
        step_min = fine_step_min if ts >= fine_from else coarse_step_min

        # AR(1) weather process: warm/cold spells persist for a couple of days
        phi = math.exp(-(step_min / 60) / WEATHER_MEMORY_HOURS)
        weather = phi * weather + math.sqrt(1 - phi**2) * WEATHER_SIGMA * rng.gauss(0, 1)

        seasonal = _seasonal(ts)
        diurnal = _diurnal(ts, seasonal)
        temperature = (
            ANNUAL_MEAN + sensor["bias"]
            + sensor["seasonal_scale"] * (seasonal - ANNUAL_MEAN)
            + sensor["diurnal_scale"] * diurnal
            + sensor["weather_scale"] * weather
            + rng.gauss(0, sensor["noise"])
        )
        # Humidity: higher at night/cold/overcast, lower in the warm afternoon
        humidity = (
            72 - 1.6 * diurnal - 0.5 * (seasonal - ANNUAL_MEAN)
            - 0.8 * weather + rng.gauss(0, 1.5)
        )
        if sensor["id"] == "mock-indoor":
            humidity = 45 + 0.3 * (humidity - 72) + rng.gauss(0, 1)

        yield {
            "sensor_id": sensor["id"],
            "temperature": round(temperature, 2),
            "humidity": round(min(100.0, max(20.0, humidity)), 1),
            "timestamp": ts,
        }
        ts += timedelta(minutes=step_min)


def seed_mock_data(days=400, fine_days=14, fine_step_min=10, coarse_step_min=60, seed=42, refresh=False):
    """Insert mock sensors + readings"""

    db.create_all()  # no-op for existing tables (skip/remove if you use migrations only)

    now = datetime.now().replace(second=0, microsecond=0)
    now -= timedelta(minutes=now.minute % fine_step_min)
    start = now - timedelta(days=days)
    fine_from = now - timedelta(days=fine_days)

    total = 0
    for sensor in MOCK_SENSORS:
        if not db.session.get(Sensor, sensor["id"]):
            db.session.add(Sensor(**{k: sensor[k] for k in ("id", "name", "sensor_id", "location", "description")}))

        existing = TemperatureReading.query.filter_by(sensor_id=sensor["id"])
        if existing.count() and not refresh:
            print(f"[seed] {sensor['id']}: data already present, skipping (use --refresh to regenerate)")
            continue
        if refresh:
            existing.delete()

        rng = random.Random(f"{seed}:{sensor['id']}")  # deterministic per sensor
        batch, count = [], 0
        for row in generate_readings(sensor, start, now, fine_from, fine_step_min, coarse_step_min, rng):
            batch.append(row)
            if len(batch) >= 5000:
                db.session.bulk_insert_mappings(TemperatureReading, batch)
                count += len(batch)
                batch = []
        if batch:
            db.session.bulk_insert_mappings(TemperatureReading, batch)
            count += len(batch)
        db.session.commit()
        total += count
        print(f"[seed] {sensor['id']}: inserted {count} readings ({start:%Y-%m-%d} -> {now:%Y-%m-%d %H:%M})")

    db.session.commit()
    print(f"[seed] done, {total} readings inserted")
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=400, help="history length in days (default 400)")
    parser.add_argument("--fine-days", type=int, default=14, help="days of high-resolution data (default 14)")
    parser.add_argument("--fine-step", type=int, default=10, help="minutes between fine readings (default 10)")
    parser.add_argument("--coarse-step", type=int, default=60, help="minutes between older readings (default 60)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducible data")
    parser.add_argument("--refresh", action="store_true", help="delete and regenerate mock sensors' readings")
    args = parser.parse_args()

    from app import create_app

    app = create_app()
    with app.app_context():
        seed_mock_data(args.days, args.fine_days, args.fine_step, args.coarse_step, args.seed, args.refresh)


if __name__ == "__main__":
    main()
