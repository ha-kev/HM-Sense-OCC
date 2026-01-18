from typing import List

from pydantic import BaseModel

from .feature_vector_response import FeatureVectorResponse
from .sensor import Sensor


class FeatureVectorsResult(BaseModel):
    feature_vectors: List[FeatureVectorResponse]
    current_sensors: List[Sensor]
