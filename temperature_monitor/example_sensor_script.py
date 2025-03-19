"""
This script reads temperature data from a 1-wire sensor connected to a Raspberry Pi
and sends it to the API server. It should be scheduled to run at regular intervals.
"""
import os
import time
import requests
import json
from datetime import datetime

# 1-wire sensor configuration
SENSOR_ID = "28-00000abcdef"  # Replace with actual sensor ID
W1_DEVICE_PATH = f"/sys/bus/w1/devices/{SENSOR_ID}/w1_slave"

# API configuration
API_URL = "http://localhost:5000/api/temperature"
API_TOKEN = os.environ.get("API_TOKEN", "your-jwt-token-here")

def read_temp():
   """Read temperature from 1-wire sensor"""
   try:
      with open(W1_DEVICE_PATH, 'r') as f:
         lines = f.readlines()

      # Check if CRC check is successful (first line ends with 'YES')
      if lines[0].strip()[-3:] != 'YES':
         raise ValueError("CRC check failed")

      # Extract temperature from second line
      temp_pos = lines[1].find('t=')
      if temp_pos == -1:
         raise ValueError("Temperature data not found")

      # Convert to Celsius (value is in millidegrees)
      temp_string = lines[1][temp_pos + 2:]
      temp_c = float(temp_string) / 1000.0

      return temp_c
   except Exception as e:
      print(f"Error reading temperature: {e}")
      return None

def send_to_api(temperature):
   """Send temperature data to API"""
   payload = {
      "sensor_id": SENSOR_ID,
      "temperature": temperature,
      "humidity": None  # This sensor doesn't provide humidity
   }

   headers = {
      "Authorization": f"Bearer {API_TOKEN}",
      "Content-Type": "application/json"
   }

   try:
      response = requests.post(API_URL, json=payload, headers=headers)
      if response.status_code == 201:
         print(f"Temperature data sent successfully: {temperature}°C")
      else:
         print(f"Error sending data: {response.status_code}, {response.text}")
   except Exception as e:
      print(f"Exception when sending data: {e}")

def main():
   # Read temperature from sensor
   temperature = read_temp()

   if temperature is not None:
      # Send to API
      send_to_api(temperature)
   else:
      print("Failed to get temperature reading")

if __name__ == "__main__":
   main()