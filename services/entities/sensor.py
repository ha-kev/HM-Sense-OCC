from typing import Optional
from pydantic import BaseModel, Field, validator
try:  # Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # Pydantic v1
    ConfigDict = None
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
            iso_value = cls._normalize_fractional_seconds(iso_value)
            return int(datetime.fromisoformat(iso_value).timestamp())
        raise TypeError("Unsupported timestamp type")

    @staticmethod
    def _normalize_fractional_seconds(iso_value: str) -> str:
        if "." not in iso_value:
            return iso_value
        main, fractional_and_tz = iso_value.split(".", 1)
        tz_sign = ""
        tz_value = ""
        for sign in ("+", "-"):
            if sign in fractional_and_tz:
                frac_part, tz_value = fractional_and_tz.split(sign, 1)
                tz_sign = sign
                break
        else:
            frac_part = fractional_and_tz
        frac_part = (frac_part[:6]).ljust(6, "0")
        if tz_sign:
            return f"{main}.{frac_part}{tz_sign}{tz_value}"
        return f"{main}.{frac_part}"

    if ConfigDict is not None:
        model_config = ConfigDict(populate_by_name=True)
    else:
        class Config:  # type: ignore[override]
            allow_population_by_field_name = True