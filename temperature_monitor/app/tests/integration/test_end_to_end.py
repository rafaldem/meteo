import pytest
import json
from datetime import datetime

def test_end_to_end_temperature_workflow(client):
   """Test the complete workflow from registration to temperature queries."""
   # 1. Register a new admin user
   response = client.post('/auth/register',
                          json={
                             'username': 'e2e_admin',
                             'email': 'e2e_admin@example.com',
                             'password': 'password123'
                          })
   assert response.status_code == 201

   # 2. Login with the new user
   response = client.post('/auth/login',
                          json={
                             'username': 'e2e_admin',
                             'password': 'password123'
                          })
   assert response.status_code == 200
   data = json.loads(response.data)
   access_token = data['access_token']
   headers = {'Authorization': f'Bearer {access_token}'}

   # 3. Add a temperature reading
   response = client.post('/api/temperature',
                          headers=headers,
                          json={
                             'sensor_id': 'e2e-sensor',
                             'temperature': 24.5,
                             'humidity': 65.0
                          })
   assert response.status_code == 201

   # 4. Query temperature data
   response = client.get('/api/temperature/e2e-sensor?timeframe=daily',
                         headers=headers)
   assert response.status_code == 200
   data = json.loads(response.data)
   assert data['sensor_id'] == 'e2e-sensor'

   # 5. Update user profile
   response = client.put('/auth/profile',
                         headers=headers,
                         json={
                            'theme': 'dark',
                            'dashboard_layout': 'compact'
                         })
   assert response.status_code == 200
   data = json.loads(response.data)
   assert data['theme'] == 'dark'
   assert data['dashboard_layout'] == 'compact'

   # 6. Add an application setting
   response = client.post('/admin/settings',
                          headers=headers,
                          json={
                             'key': 'e2e_setting',
                             'value': 'test_value',
                             'description': 'E2E test setting',
                             'requires_admin': False
                          })
   assert response.status_code == 201

   # 7. Register a regular user
   response = client.post('/auth/register',
                          json={
                             'username': 'e2e_user',
                             'email': 'e2e_user@example.com',
                             'password': 'password123'
                          })
   assert response.status_code == 201

   # 8. Login with regular user
   response = client.post('/auth/login',
                          json={
                             'username': 'e2e_user',
                             'password': 'password123'
                          })
   assert response.status_code == 200
   data = json.loads(response.data)
   user_access_token = data['access_token']
   user_headers = {'Authorization': f'Bearer {user_access_token}'}

   # 9. Regular user can query temperature data
   response = client.get('/api/temperature/e2e-sensor?timeframe=daily',
                         headers=user_headers)
   assert response.status_code == 200

   # 10. But regular user cannot add temperature data
   response = client.post('/api/temperature',
                          headers=user_headers,
                          json={
                             'sensor_id': 'e2e-sensor-2',
                             'temperature': 25.0,
                             'humidity': 60.0
                          })
   assert response.status_code == 403  # Forbidden

   # 11. Regular user can update non-admin settings
   response = client.put('/admin/settings/e2e_setting',
                         headers=user_headers,
                         json={
                            'value': 'updated_value'
                         })
   assert response.status_code == 200

   # 12. Admin can update any user's data
   response = client.put(f'/admin/users/2',
                         headers=headers,
                         json={
                            'theme': 'light'
                         })
   assert response.status_code == 200

def test_refactored_code_quality(app):
   """Test that refactored code meets quality standards."""
   # This is more of a code inspection than a test
   # In a real project, we would use linters and static analyzers

   # Check import patterns and organization
   from app import create_app, db
   from app.models import User, UserRole, TemperatureReading, AppSettings

   # Check that models use correct relationships
   with app.app_context():
      # Verify model relationships and constraints
      assert User.__tablename__ == 'user'
      assert TemperatureReading.__tablename__ == 'temperature_reading'

      # Verify indexes for performance
      from sqlalchemy import inspect
      inspector = inspect(db.engine)

      user_indexes = inspector.get_indexes('user')
      temp_indexes = inspector.get_indexes('temperature_reading')

      # Check for expected indexes
      user_indexed_columns = [idx['column_names'][0] for idx in user_indexes]
      temp_indexed_columns = [idx['column_names'][0] for idx in temp_indexes]

      assert 'username' in user_indexed_columns
      assert 'email' in user_indexed_columns
      assert 'sensor_id' in temp_indexed_columns
      assert 'timestamp' in temp_indexed_columns