from typing import Dict

from pydantic import BaseModel

class PredictionResponse(BaseModel):
    sensor_id: str
    state: int
    state_label: str
    state_probabilities: Dict[str, float]