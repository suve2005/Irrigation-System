# schemas.py
from pydantic import BaseModel

class SensorPayload(BaseModel):
    node_id: int
    recorded_at: str
    soil_moisture_vwc: float
    soil_temp: float
    canopy_air_temp: float
    canopy_rh: float
    battery_voltage: float