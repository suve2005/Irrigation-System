from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import date
from database import get_db_connection
from schemas import SensorPayload
from feature_engineering import calculate_and_store_features
from model import run_inference_from_db

app = FastAPI(title="Irrigation API")

# ---- CORS SECURITY OVERRIDE ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows your local HTML file to fetch data
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/sensor-reading")
def receive_sensor_data(payload: SensorPayload, background_tasks: BackgroundTasks):
    # Save raw data
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO sensor_reading (node_id, recorded_at, soil_moisture_vwc, soil_temp)
        VALUES (%s, %s, %s, %s)
    """, (payload.node_id, payload.recorded_at, payload.soil_moisture_vwc, payload.soil_temp))
    db.commit()
    db.close()
    
    # Trigger pipeline
    background_tasks.add_task(trigger_pipeline, date.today())
    return {"status": "success"}

def trigger_pipeline(target_date: date):
    calculate_and_store_features(1, 1, target_date)
    run_inference_from_db(target_date)

# ---- FRONTEND / ESP32 ENDPOINT ----
@app.get("/api/latest-command")
def get_latest_command():
    """Frontend and ESP32 can call this to see the latest model decision."""
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    # Get the newest prediction
    cursor.execute("SELECT water_needed_mm, pump_run_time_min, predicted_at FROM prediction ORDER BY prediction_id DESC LIMIT 1")
    result = cursor.fetchone()
    db.close()
    
    if result:
        return result
    return {"error": "No predictions available yet."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)