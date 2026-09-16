# main.py
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from datetime import date
from database import get_db_connection
from schemas import SensorPayload
from feature_engineering import calculate_and_store_features
from model import run_inference_from_db

app = FastAPI(title="Irrigation API")

@app.post("/api/sensor-reading")
def receive_sensor_data(payload: SensorPayload, background_tasks: BackgroundTasks):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO sensor_reading (node_id, recorded_at, soil_moisture_vwc, soil_temp, canopy_air_temp, canopy_rh, battery_voltage)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (payload.node_id, payload.recorded_at, payload.soil_moisture_vwc, payload.soil_temp, payload.canopy_air_temp, payload.canopy_rh, payload.battery_voltage))
    db.commit()
    db.close()

    print(f"[SERVER] Received & saved raw data for Node {payload.node_id}")

    # Trigger pipeline async
    today = date.today()
    background_tasks.add_task(trigger_pipeline, today)

    return {"status": "success"}

def trigger_pipeline(target_date: date):
    calculate_and_store_features(plot_id=1, cycle_id=1, target_date=target_date)
    run_inference_from_db(target_date=target_date)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)