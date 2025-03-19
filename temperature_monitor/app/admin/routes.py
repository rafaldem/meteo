from flask import request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.admin import bp
from app.models import User, UserRole, AppSettings
from app.utils.decorators import admin_required

@bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
   users = User.query.all()
   return jsonify({'users': [user.to_dict() for user in users]}), 200

@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
   user = User.query.get(user_id)

   if not user:
      return jsonify({'error': 'User not found'}), 404

   data = request.get_json()
   allowed_fields = ['email', 'role', 'theme', 'dashboard_layout']

   for field in allowed_fields:
      if field in data:
         if field == 'role':
            try:
               role_value = data['role']
               user.role = UserRole(role_value)
            except ValueError:
               return jsonify({'error': f'Invalid role: {role_value}'}), 400
         else:
            setattr(user, field, data[field])

   # Handle password reset separately
   if 'new_password' in data:
      user.password_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')

   db.session.commit()
   return jsonify(user.to_dict()), 200

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
   user = User.query.get(user_id)

   if not user:
      return jsonify({'error': 'User not found'}), 404

   db.session.delete(user)
   db.session.commit()

   return jsonify({'message': 'User deleted successfully'}), 200

@bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
   settings = AppSettings.query.all()
   return jsonify({'settings': [setting.to_dict() for setting in settings]}), 200

@bp.route('/settings', methods=['POST'])
@jwt_required()
@admin_required
def add_setting():
   data = request.get_json()

   if not all(k in data for k in ('key', 'value')):
      return jsonify({'error': 'Missing required fields'}), 400

   # Check if setting already exists
   existing = AppSettings.query.filter_by(key=data['key']).first()
   if existing:
      return jsonify({'error': f'Setting with key {data["key"]} already exists'}), 400

   setting = AppSettings(
      key=data['key'],
      value=data['value'],
      description=data.get('description', ''),
      requires_admin=data.get('requires_admin', False)
   )

   db.session.add(setting)
   db.session.commit()

   return jsonify(setting.to_dict()), 201

@bp.route('/settings/<key>', methods=['PUT'])
@jwt_required()
def update_setting(key):
   from flask_jwt_extended import get_jwt_identity

   current_user_id = get_jwt_identity()
   user = User.query.get(current_user_id)
   setting = AppSettings.query.filter_by(key=key).first()

   if not setting:
      return jsonify({'error': 'Setting not found'}), 404

   # Check permissions
   if setting.requires_admin and user.role != UserRole.ADMIN:
      return jsonify({'error': 'Admin privileges required to modify this setting'}), 403

   data = request.get_json()
   if 'value' in data:
      setting.value = data['value']

   if 'description' in data and user.role == UserRole.ADMIN:
      setting.description = data['description']

   if 'requires_admin' in data and user.role == UserRole.ADMIN:
      setting.requires_admin = data['requires_admin']

   db.session.commit()
   return jsonify(setting.to_dict()), 200
