from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Sensor(BaseModel):
    sensor_id: str = Field(alias='sensorId')
    timestamp: int
    humidity: Optional[float] = None
    temperature: Optional[float] = None
    co2: Optional[float] = None
    motion: Optional[float] = None
    light: Optional[float] = None
    schema_version: int = 1
    
    @validator("timestamp", pre=True)
    def _parse_timestamp(cls, value):
        if isinstance(value, int):
            return value
        if isinstance(value, datetime):
            return int(value.timestamp())
        if isinstance(value, str):
            iso_value = value.replace("Z", "+00:00") if value.endswith("Z") else value
            return int(datetime.fromisoformat(iso_value).timestamp())
        raise TypeError("Unsupported timestamp type")