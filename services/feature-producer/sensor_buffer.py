from collections import deque
from typing import Deque
from entities.sensor import Sensor
import pandas as pd

class SensorBuffer:
    def __init__(self, max_hours: int = 3):
        self.buffer: Deque[Sensor] = deque(maxlen=max_hours * 12)  # 3h at 5min intervals (36 datapoints)
    
    def add(self, sensor: Sensor):
        self.buffer.append(sensor)
    
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([s.model_dump() for s in self.buffer])
    
    def get_last_n_minutes(self, minutes: int) -> pd.DataFrame:
        df = self.to_dataframe()
        cutoff = df['timestamp'].max() - (minutes * 60)
        return df[df['timestamp'] >= cutoff]