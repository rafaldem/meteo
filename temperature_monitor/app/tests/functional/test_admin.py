import pytest
import json
from app.models import User, UserRole, AppSettings

def test_get_users_admin(client, admin_headers):
   """Test getting all users as admin."""
   response = client.get('/admin/users', headers=admin_headers)

   assert response.status_code == 200
   data = json.loads(response.data)
   assert 'users' in data
   assert len(data['users']) >= 2  # admin and regular user at minimum

   # Check user data structure
   user_data = next((user for user in data['users'] if user['username'] == 'admin'), None)
   assert user_data is not None
   assert user_data['role'] == 'admin'

def test_get_users_unauthorized(client, user_headers):
   """Test getting all users as regular user."""
   response = client.get('/admin/users', headers=user_headers)

   # Should fail because regular users can't access admin endpoints
   assert response.status_code == 403
   data = json.loads(response.data)
   assert 'error' in data
   assert data['error'] == 'Admin privileges required'

def test_update_user(client, admin_headers, db_session):
   """Test updating a user as admin."""
   # Get the user to update
   user = User.query.filter_by(username='user').first()

   response = client.put(f'/admin/users/{user.id}',
                         headers=admin_headers,
                         json={
                            'email': 'updated_user@example.com',
                            'theme': 'dark',
                            'role': 'admin'  # Change role to admin
                         })

   assert response.status_code == 200
   data = json.loads(response.data)
   assert data['email'] == 'updated_user@example.com'
   assert data['theme'] == 'dark'
   assert data['role'] == 'admin'

   # Verify changes in database
   updated_user = User.query.get(user.id)
   assert updated_user.email == 'updated_user@example.com'
   assert updated_user.theme == 'dark'
   assert updated_user.role == UserRole.ADMIN

def test_delete_user(client, admin_headers, db_session):
   """Test deleting a user as admin."""
   # First create a user to delete
   new_user = User(
      username='to_delete',
      email='to_delete@example.com',
      password_hash='hashed_password',
      role=UserRole.USER
   )
   db_session.add(new_user)
   db_session.commit()

   user_id = new_user.id

   response = client.delete(f'/admin/users/{user_id}', headers=admin_headers)

   assert response.status_code == 200
   data = json.loads(response.data)
   assert 'message' in data
   assert data['message'] == 'User deleted successfully'

   # Verify user was deleted from database
   deleted_user = User.query.get(user_id)
   assert deleted_user is None

def test_get_settings(client, user_headers):
   """Test getting application settings."""
   response = client.get('/admin/settings', headers=user_headers)

   assert response.status_code == 200
   data = json.loads(response.data)
   assert 'settings' in data
   assert len(data['settings']) >= 2  # sampling_rate and display_units at minimum

def test_add_setting(client, admin_headers, db_session):
   """Test adding a new application setting."""
   response = client.post('/admin/settings',
                          headers=admin_headers,
                          json={
                             'key': 'notification_threshold',
                             'value': '30',
                             'description': 'Temperature threshold for notifications',
                             'requires_admin': False
                          })

   assert response.status_code == 201
   data = json.loads(response.data)
   assert data['key'] == 'notification_threshold'
   assert data['value'] == '30'

   # Verify in database
   setting = AppSettings.query.filter_by(key='notification_threshold').first()
   assert setting is not None
   assert setting.value == '30'
   assert setting.requires_admin is False

def test_update_setting_admin(client, admin_headers, db_session):
   """Test updating an application setting as admin."""
   response = client.put('/admin/settings/sampling_rate',
                         headers=admin_headers,
                         json={
                            'value': '600',
                            'description': 'Updated description',
                            'requires_admin': True
                         })

   assert response.status_code == 200
   data = json.loads(response.data)
   assert data['value'] == '600'
   assert data['description'] == 'Updated description'

   # Verify in database
   setting = AppSettings.query.filter_by(key='sampling_rate').first()
   assert setting.value == '600'
   assert setting.description == 'Updated description'

def test_update_setting_user(client, user_headers, db_session):
   """Test updating a non-admin setting as regular user."""
   response = client.put('/admin/settings/display_units',
                         headers=user_headers,
                         json={
                            'value': 'fahrenheit'
                         })

   assert response.status_code == 200
   data = json.loads(response.data)
   assert data['value'] == 'fahrenheit'

   # Verify in database
   setting = AppSettings.query.filter_by(key='display_units').first()
   assert setting.value == 'fahrenheit'

def test_update_admin_setting_as_user(client, user_headers):
   """Test updating an admin-only setting as regular user."""
   response = client.put('/admin/settings/sampling_rate',
                         headers=user_headers,
                         json={
                            'value': '1200'
                         })

   # Should fail because regular users can't update admin-only settings
   assert response.status_code == 403
   data = json.loads(response.data)
   assert 'error' in data
   assert data['error'] == 'Admin privileges required to modify this setting'
