import pytest
import json

def test_input_validation_registration(client):
   """Test input validation for registration."""
   # Test missing fields
   response = client.post('/auth/register',
                          json={
                             'username': 'test_validation'
                             # Missing email and password
                          })

   assert response.status_code == 400

   # Test invalid email format
   response = client.post('/auth/register',
                          json={
                             'username': 'test_validation',
                             'email': 'invalid-email',
                             'password': 'password123'
                          })

   assert response.status_code == 400

def test_input_validation_temperature(client, admin_headers):
   """Test input validation for temperature readings."""
   # Test missing fields
   response = client.post('/api/temperature',
                          headers=admin_headers,
                          json={
                             # Missing sensor_id
                             'temperature': 22.5
                          })

   assert response.status_code == 400

   # Test invalid temperature value
   response = client.post('/api/temperature',
                          headers=admin_headers,
                          json={
                             'sensor_id': 'test-sensor',
                             'temperature': "not a number"
                          })

   assert response.status_code in [400, 422]  # Either bad request or unprocessable entity
