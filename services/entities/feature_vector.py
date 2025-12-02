from dataclasses import dataclass

@dataclass(frozen=True)
class FeatureVector:
    sensor_id: str
    timestamp: int
    humidity: float
    temperature: float
    co2: float
    motion: float
    light: float
    # Humidity
    avg_humidity_60m: float
    avg_humidity_120m: float
    avg_humidity_180m: float
    std_humidity: float
    # Temperature
    avg_temperature: float
    max_temperature: float
    min_temperature: float
    std_temperature: float
    # CO2
    avg_co2_60m: float
    max_co2_60m: float
    min_co2_60m: float
    std_co2_60m: float
    residual_co2: float # co2_current - co2_trend
    delta_5m_co2: float # per minute rate (delta_k / (5*k)
    delta_30m_co2: float
    delta_60m_co2: float
    # Motion (Timeframe 30 min)
    avg_motion: float
    max_motion: float
    std_motion: float
    count_motion_10m: float
    count_motion_30m: float
    recent_motion_10m: int #(bool, 1 True, 0 False)
    # Light
    light_level: int # 0, 1, 2, 3 (Splited up on 4 LUX - 2000 LUX)
    daylight_factor: float
    # Time Base
    hour_of_day: int
    day_of_week: int
    is_weekend: int
    is_off_hours: int
    is_night: int
    season: int # Spring 0, Summer 1, Autumn 2, Winter 3
    # Cross Sensor
    residual_co2_recent_motion: float # residual motion x recent motion
    rising_co2_recent_motion: float # co2 trend x recent motion
    light_recent_motion: float # multiply light with last motion
    temperature_humidity: float # temperature x humidity
    motion_off_hours: float # motion x is_off_hours
    light_on_at_night: float # light threshhold x is_night
    
    schema_version: int = 1