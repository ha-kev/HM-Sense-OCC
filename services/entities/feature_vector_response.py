from dataclasses import asdict
from pydantic import BaseModel

from .feature_vector import FeatureVector


class FeatureVectorResponse(BaseModel):
    sensor_id: str
    timestamp: int
    humidity: float
    temperature: float
    co2: float
    motion: float
    light: float
    avg_humidity_60m: float
    avg_humidity_120m: float
    avg_humidity_180m: float
    std_humidity: float
    avg_temperature: float
    max_temperature: float
    min_temperature: float
    std_temperature: float
    avg_co2_60m: float
    max_co2_60m: float
    min_co2_60m: float
    std_co2_60m: float
    residual_co2: float
    delta_5m_co2: float
    delta_30m_co2: float
    delta_60m_co2: float
    avg_motion: float
    max_motion: float
    std_motion: float
    count_motion_10m: float
    count_motion_30m: float
    recent_motion_10m: int
    light_level: int
    daylight_factor: float
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    is_off_hours: int
    is_night: int
    season: int
    residual_co2_recent_motion: float
    rising_co2_recent_motion: float
    light_recent_motion: float
    temperature_humidity: float
    motion_off_hours: float
    light_on_at_night: float
    schema_version: int

    @classmethod
    def from_model(cls, vector: FeatureVector) -> "FeatureVectorResponse":
        return cls(**asdict(vector))
