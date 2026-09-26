from pydantic import BaseModel, Field

class SensorPayload(BaseModel):
    node_id: int = Field(..., example=1)
    recorded_at: str = Field(..., example="2026-09-16 14:00:00")
    soil_moisture_vwc: float = Field(..., example=28.5)
    soil_temp: float = Field(..., example=24.2)
    canopy_air_temp: float = Field(..., example=26.0)
    canopy_rh: float = Field(..., example=65.0)
    battery_voltage: float = Field(..., example=4.1)
