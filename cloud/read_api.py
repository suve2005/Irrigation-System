from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_connection

app = FastAPI(title="Irrigation Sensor Read API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/api/sensor/{serial_number}")
def get_sensor_data(serial_number: str):
    try:
        node_id = int(serial_number)
    except ValueError:
        raise HTTPException(status_code=400, detail="Sensor ID must be a numeric node_id")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT node_id, soil_temp, soil_moisture_vwc, canopy_rh, battery_voltage
            FROM sensor_reading
            WHERE node_id = %s AND recorded_at <= NOW()
            ORDER BY recorded_at DESC, reading_id DESC
            LIMIT 1
            """,
            (node_id,),
        )
        reading = cursor.fetchone()
        if reading is None:
            raise HTTPException(status_code=404, detail="No sensor reading found for this node")

        return {
            "sensor_id": str(reading["node_id"]),
            "temperature": float(reading["soil_temp"]),
            "moisture": float(reading["soil_moisture_vwc"]),
            "humidity": float(reading["canopy_rh"]),
            "battery": float(reading["battery_voltage"]),
        }
    finally:
        cursor.close()
        connection.close()
