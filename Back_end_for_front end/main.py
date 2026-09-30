from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# Allow the React Native app to make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base values to simulate slight fluctuations rather than wild random numbers
sensor_states = {}

@app.get("/api/sensor/{serial_number}")
def get_sensor_data(serial_number: str):
    # Initialize the sensor in memory if it hasn't been polled yet
    if serial_number not in sensor_states:
        sensor_states[serial_number] = {
            "temperature": 24.0,
            "moisture": 65.0,
            "humidity": 50.0,
            "battery": 100.0
        }
    
    # Simulate realistic live hardware fluctuations
    current = sensor_states[serial_number]
    
    new_data = {
        "sensor_id": serial_number,
        "temperature": round(current["temperature"] + random.uniform(-0.2, 0.2), 1),
        "moisture": round(current["moisture"] + random.uniform(-1.0, 1.0), 1),
        "humidity": round(current["humidity"] + random.uniform(-0.5, 0.5), 1),
        "battery": max(0.0, round(current["battery"] - random.uniform(0.0, 0.1), 1))
    }
    
    # Save the new state for the next poll
    sensor_states[serial_number] = new_data
    
    return new_data