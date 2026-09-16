# esp32.py
import time
import requests
import random
from datetime import datetime

URL = "http://127.0.0.1:8000/api/sensor-reading"


def simulate_and_send():
    print("Starting ESP32 Simulation...")
    while True:
        payload = {
            "node_id": 1,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_moisture_vwc": round(random.uniform(20.0, 35.0), 2),
            "soil_temp": round(random.uniform(22.0, 28.0), 2),
            "canopy_air_temp": 25.0,
            "canopy_rh": 60.0,
            "battery_voltage": 4.1
        }

        try:
            response = requests.post(URL, json=payload)
            print(f"[ESP32] Ping sent. Server replied: {response.json()}")
        except Exception as e:
            print(f"[ESP32] Network error: {e}")

        time.sleep(10)  # Send data every 10 seconds


if __name__ == "__main__":
    simulate_and_send()