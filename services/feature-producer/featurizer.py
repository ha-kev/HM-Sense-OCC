from entities.sensor import Sensor
from entities.feature_vector import FeatureVector
from sensor_buffer import SensorBuffer
from datetime import datetime

class Featurizer:
    def __init__(self, buffer: SensorBuffer) -> None:
        self.buffer = buffer
        
    def extract_features(self, current_sensor: Sensor) -> FeatureVector:
        df_5 = self.buffer.get_last_n_minutes(5)
        df_10 = self.buffer.get_last_n_minutes(10)
        df_30 = self.buffer.get_last_n_minutes(30)
        df_60 = self.buffer.get_last_n_minutes(60)
        df_120 = self.buffer.get_last_n_minutes(120)
        df_180 = self.buffer.get_last_n_minutes(180)
        
        # Direct Values
        humidity: float = current_sensor.humidity or 0.0
        temperature: float = current_sensor.temperature or 0.0
        co2: float = current_sensor.co2 or 0.0
        motion: float = current_sensor.motion or 0.0
        light: float = current_sensor.light or 0.0
        
        # Calculated Values
        
        # Humidity
        avg_humidity_60m: float = df_60['humidity'].mean() if len(df_60) > 0 else humidity
        avg_humidity_120m: float = df_120['humidity'].mean() if len(df_120) > 0 else humidity
        avg_humidity_180m: float = df_180['humidity'].mean() if len(df_180) > 0 else humidity
        std_humidity: float = df_180['humidity'].std() if len(df_180) > 1 else 0.0
        
        # Temperature
        avg_temperature: float = df_60['temperature'].mean() if len(df_60) > 0 else temperature
        max_temperature: float = df_60['temperature'].max() if len(df_60) > 0 else temperature
        min_temperature: float = df_60['temperature'].min() if len(df_60) > 0 else temperature
        std_temperature: float = df_60['temperature'].std() if len(df_60) > 1 else 0.0
        
        # CO2
        avg_co2_60m: float = df_60['co2'].mean() if len(df_60) > 0 else co2
        max_co2_60m: float = df_60['co2'].max() if len(df_60) > 0 else co2
        min_co2_60m: float = df_60['co2'].min() if len(df_60) > 0 else co2
        std_co2_60m: float = df_60['co2'].std() if len(df_60) > 1 else 0.0
        residual_co2: float = co2 - avg_co2_60m
        
        # Delta CO2 (rate of change per minute)
        co2_5m_ago = df_5['co2'].iloc[0] if len(df_5) > 0 else co2
        co2_30m_ago = df_30['co2'].iloc[0] if len(df_30) > 0 else co2
        co2_60m_ago = df_60['co2'].iloc[0] if len(df_60) > 0 else co2
        
        delta_5m_co2: float = (co2 - co2_5m_ago) / 5.0 if len(df_5) > 0 else 0.0
        delta_30m_co2: float = (co2 - co2_30m_ago) / 30.0 if len(df_30) > 0 else 0.0
        delta_60m_co2: float = (co2 - co2_60m_ago) / 60.0 if len(df_60) > 0 else 0.0
        
        # Motion (30 min timeframe)
        avg_motion: float = df_30['motion'].mean() if len(df_30) > 0 else motion
        max_motion: float = df_30['motion'].max() if len(df_30) > 0 else motion
        std_motion: float = df_30['motion'].std() if len(df_30) > 1 else 0.0
        count_motion_10m: float = float((df_10['motion'] > 0).sum()) if len(df_10) > 0 else 0.0
        count_motion_30m: float = float((df_30['motion'] > 0).sum()) if len(df_30) > 0 else 0.0
        recent_motion_10m: int = 1 if count_motion_10m > 0 else 0
        
        # Light
        # Light level: 0-500 LUX = 0, 501-1000 = 1, 1001-1500 = 2, 1501-2000 = 3, >2000 = 3
        if light <= 500:
            light_level: int = 0
        elif light <= 1000:
            light_level = 1
        elif light <= 1500:
            light_level = 2
        else:
            light_level = 3
        
        daylight_factor: float = min(light / 2000.0, 1.0)
        
        # Time-based features
        dt = datetime.fromtimestamp(current_sensor.timestamp)
        hour_of_day: int = dt.hour
        day_of_week: int = dt.weekday()  # 0=Monday, 6=Sunday
        is_weekend: int = 1 if day_of_week >= 5 else 0
        is_off_hours: int = 1 if hour_of_day < 7 or hour_of_day >= 19 else 0
        is_night: int = 1 if hour_of_day < 6 or hour_of_day >= 22 else 0
        
        # Season: 0=Spring, 1=Summer, 2=Autumn, 3=Winter
        month = dt.month
        if 3 <= month <= 5:
            season: int = 0
        elif 6 <= month <= 8:
            season = 1
        elif 9 <= month <= 11:
            season = 2
        else:
            season = 3
        
        # Cross-sensor interaction features
        residual_co2_recent_motion: float = residual_co2 * recent_motion_10m
        rising_co2_recent_motion: float = delta_5m_co2 * recent_motion_10m
        light_recent_motion: float = light * recent_motion_10m
        temperature_humidity: float = temperature * humidity
        motion_off_hours: float = motion * is_off_hours
        light_on_at_night: float = (1.0 if light > 50 else 0.0) * is_night
        
        return FeatureVector(
            sensor_id=current_sensor.sensor_id,
            timestamp=current_sensor.timestamp,
            humidity=humidity,
            temperature=temperature,
            co2=co2,
            motion=motion,
            light=light,
            avg_humidity_60m=avg_humidity_60m,
            avg_humidity_120m=avg_humidity_120m,
            avg_humidity_180m=avg_humidity_180m,
            std_humidity=std_humidity,
            avg_temperature=avg_temperature,
            max_temperature=max_temperature,
            min_temperature=min_temperature,
            std_temperature=std_temperature,
            avg_co2_60m=avg_co2_60m,
            max_co2_60m=max_co2_60m,
            min_co2_60m=min_co2_60m,
            std_co2_60m=std_co2_60m,
            residual_co2=residual_co2,
            delta_5m_co2=delta_5m_co2,
            delta_30m_co2=delta_30m_co2,
            delta_60m_co2=delta_60m_co2,
            avg_motion=avg_motion,
            max_motion=max_motion,
            std_motion=std_motion,
            count_motion_10m=count_motion_10m,
            count_motion_30m=count_motion_30m,
            recent_motion_10m=recent_motion_10m,
            light_level=light_level,
            daylight_factor=daylight_factor,
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            is_weekend=is_weekend,
            is_off_hours=is_off_hours,
            is_night=is_night,
            season=season,
            residual_co2_recent_motion=residual_co2_recent_motion,
            rising_co2_recent_motion=rising_co2_recent_motion,
            light_recent_motion=light_recent_motion,
            temperature_humidity=temperature_humidity,
            motion_off_hours=motion_off_hours,
            light_on_at_night=light_on_at_night,
            schema_version=1
        )