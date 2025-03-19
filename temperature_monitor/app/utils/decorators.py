from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User, UserRole

def admin_required(f):
   @wraps(f)
   def decorated_function(*args, **kwargs):
      current_user_id = get_jwt_identity()
      user = User.query.get(current_user_id)

      if not user or user.role != UserRole.ADMIN:
         return jsonify({'error': 'Admin privileges required'}), 403

      return f(*args, **kwargs)

   return decorated_function
