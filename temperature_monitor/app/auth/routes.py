from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

from app import db, bcrypt
from app.auth import bp
from app.models import User, UserRole


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate input
    if not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    # Create new user
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    # First user gets admin role, others get user role
    role = UserRole.ADMIN if User.query.count() == 0 else UserRole.USER

    user = User(username=data["username"], email=data["email"], password_hash=hashed_password, role=role)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not all(k in data for k in ("username", "password")):
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=data["username"]).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}), 200


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)

    return jsonify({"access_token": access_token}), 200


@bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    allowed_fields = ["email", "theme", "dashboard_layout"]

    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    # Handle password change separately for security
    if "old_password" in data and "new_password" in data:
        if not bcrypt.check_password_hash(user.password_hash, data["old_password"]):
            return jsonify({"error": "Invalid current password"}), 400

        user.password_hash = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")

    db.session.commit()
    return jsonify(user.to_dict()), 200
