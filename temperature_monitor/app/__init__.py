from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app(config_class=Config):
   app = Flask(__name__)
   app.config.from_object(config_class)

   db.init_app(app)
   jwt.init_app(app)
   bcrypt.init_app(app)

   from app.auth import bp as auth_bp
   from app.api import bp as api_bp
   from app.admin import bp as admin_bp

   app.register_blueprint(auth_bp, url_prefix='/auth')
   app.register_blueprint(api_bp, url_prefix='/api')
   app.register_blueprint(admin_bp, url_prefix='/admin')

   @app.before_first_request
   def create_tables():
      db.create_all()

   return app
