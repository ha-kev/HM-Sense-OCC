from typing import Optional
from pydantic import BaseModel, Field

class Sensor(BaseModel):
    sensor_id: str = Field(alias='sensorId')
    timestamp: int
    humidity: Optional[float]
    temperature: Optional[float]
    co2: Optional[float]
    motion: Optional[float]
    light: Optional[float]
    schema_version: int = 1