from datetime import datetime
from app import db
from enum import Enum

class UserRole(Enum):
   ADMIN = 'admin'
   USER = 'user'

class User(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   username = db.Column(db.String(64), index=True, unique=True, nullable=False)
   email = db.Column(db.String(120), index=True, unique=True, nullable=False)
   password_hash = db.Column(db.String(128), nullable=False)
   role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
   updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   # User preferences
   theme = db.Column(db.String(20), default='light')
   dashboard_layout = db.Column(db.String(50), default='default')

   def to_dict(self):
      return {
         'id': self.id,
         'username': self.username,
         'email': self.email,
         'role': self.role.value,
         'theme': self.theme,
         'dashboard_layout': self.dashboard_layout,
         'created_at': self.created_at.isoformat(),
         'updated_at': self.updated_at.isoformat()
      }

class TemperatureReading(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   sensor_id = db.Column(db.String(64), index=True, nullable=False)
   temperature = db.Column(db.Float, nullable=False)
   humidity = db.Column(db.Float, nullable=True)
   timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

   def to_dict(self):
      return {
         'id': self.id,
         'sensor_id': self.sensor_id,
         'temperature': self.temperature,
         'humidity': self.humidity,
         'timestamp': self.timestamp.isoformat()
      }

class AppSettings(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   key = db.Column(db.String(64), unique=True, nullable=False)
   value = db.Column(db.String(255))
   description = db.Column(db.String(255))
   requires_admin = db.Column(db.Boolean, default=False)

   def to_dict(self):
      return {
         'id': self.id,
         'key': self.key,
         'value': self.value,
         'description': self.description,
         'requires_admin': self.requires_admin
      }
