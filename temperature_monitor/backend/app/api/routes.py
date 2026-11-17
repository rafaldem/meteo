from datetime import datetime, timedelta

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from version import __version__
from api import bp
from models import TemperatureReading, User, UserRole


@bp.route("/temperature", methods=["POST"])
@jwt_required()
def add_temperature():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # Only allow admins to add temperature readings
    if user.role != UserRole.ADMIN:
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.get_json()

    if not all(k in data for k in ("sensor_id", "temperature")):
        return jsonify({"error": "Missing required fields"}), 400

    reading = TemperatureReading(
        sensor_id=data["sensor_id"], temperature=data["temperature"], humidity=data.get("humidity")
    )

    db.session.add(reading)
    db.session.commit()

    return jsonify(reading.to_dict()), 201


@bp.route("/temperature/<sensor_id>", methods=["GET"])
@jwt_required()
def get_temperature(sensor_id):
    timeframe_params = ["daily", "weekly", "monthly", "yearly"]
    timeframe = request.args.get("timeframe", "daily")
    date_str = request.args.get("date")
    if timeframe not in timeframe_params:
        return (
            jsonify({"error": f"Invalid timeframe parameter." f' Should be one of: {", ".join(timeframe_params)}.'}),
            422,
        )

    if date_str:
        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        base_date = datetime.now()

    if timeframe == "daily":
        start_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        group_by = func.strftime("%H", TemperatureReading.timestamp)
    elif timeframe == "weekly":
        start_date = base_date - timedelta(days=base_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)
        group_by = func.strftime("%w", TemperatureReading.timestamp)
    elif timeframe == "monthly":
        start_date = base_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        group_by = func.strftime("%d", TemperatureReading.timestamp)
    elif timeframe == "yearly":
        start_date = base_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(year=start_date.year + 1)
        group_by = func.strftime("%m", TemperatureReading.timestamp)
    else:
        return jsonify({"error": "Invalid timeframe. Use daily, weekly, monthly, or yearly"}), 400

    readings = (
        db.session.query(
            group_by.label("time_group"),
            func.avg(TemperatureReading.temperature).label("avg_temperature"),
            func.min(TemperatureReading.temperature).label("min_temperature"),
            func.max(TemperatureReading.temperature).label("max_temperature"),
            func.avg(TemperatureReading.humidity).label("avg_humidity"),
        )
        .filter(
            TemperatureReading.sensor_id == sensor_id,
            TemperatureReading.timestamp >= start_date,
            TemperatureReading.timestamp < end_date,
        )
        .group_by("time_group")
        .all()
    )

    # Format response
    round_value = lambda x: round(x, 2) if x is not None else None
    result = {
        "sensor_id": sensor_id,
        "timeframe": timeframe,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data": [
            {
                "time_group": r.time_group,
                "avg_temperature": round_value(r.avg_temperature),
                "min_temperature": round_value(r.min_temperature),
                "max_temperature": round_value(r.max_temperature),
                "avg_humidity": round_value(r.avg_humidity),
            }
            for r in readings
        ],
    }

    return jsonify(result), 200


@bp.route("/sensors", methods=["GET"])
@jwt_required()
def get_sensors():
    sensors = db.session.query(TemperatureReading.sensor_id).distinct().all()
    sensor_ids = [s.sensor_id for s in sensors]

    return jsonify({"sensors": sensor_ids}), 200


@bp.route('/api/version')
def get_version():
    return jsonify({"version": __version__})