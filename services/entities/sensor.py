from typing import Optional
from pydantic import BaseModel

class Sensor(BaseModel):
    sensor_id: str
    timestamp: int
    humidity: Optional[float]
    temperature: Optional[float]
    co2: Optional[float]
    motion: Optional[float]
    light: Optional[float]
    