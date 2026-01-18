from typing import List

from pydantic import BaseModel

from .prediction_response import PredictionResponse
from .sensor import Sensor


class PredictionResult(BaseModel):
    predictions: List[PredictionResponse]
    current_sensors: List[Sensor]
