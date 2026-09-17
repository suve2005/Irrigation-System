import time
import requests
import random
from datetime import datetime

URL_POST = "http://127.0.0.1:8000/api/sensor-reading"
URL_GET = "http://127.0.0.1:8000/api/latest-command"

def simulate_and_send():
    print("Starting ESP32 Simulation (Two-way communication)...")
    while True:
        # 1. Push Sensor Data
        payload = {
            "node_id": 1,
            "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "soil_moisture_vwc": round(random.uniform(20.0, 35.0), 2),
            "soil_temp": 24.5, "canopy_air_temp": 25.0, "canopy_rh": 60.0, "battery_voltage": 4.1
        }
        
        try:
            requests.post(URL_POST, json=payload)
            print("[ESP32] Pushed sensor data to server.")
            
            # 2. Check for Sprinkler Commands (Polling)
            time.sleep(2) # Give server 2 seconds to run the ML model
            response = requests.get(URL_GET).json()
            
            run_time = response.get("pump_run_time_min", 0)
            if run_time > 0:
                print(f"[HARDWARE ACTION] Turning Relay ON for {run_time} minutes!")
            else:
                print("[HARDWARE ACTION] No water needed right now.")
                
        except Exception as e:
            print(f"[ESP32] Network error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    simulate_and_send()