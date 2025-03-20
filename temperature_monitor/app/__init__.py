from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()


def init_database(app):
    """Initialize the database tables."""
    with app.app_context():
        db.create_all()


def create_app(config_class=Config, init_db=True):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    from app.auth import bp as auth_bp
    from app.api import bp as api_bp
    from app.admin import bp as admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Initialize database if requested
    if init_db:
        init_database(app)

    return app