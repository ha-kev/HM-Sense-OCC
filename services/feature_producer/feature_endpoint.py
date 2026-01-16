from typing import List, Optional

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from .api_client import APIClient
from .featurizer import Featurizer
from .measurement_parser import flatten_measurements
from ..entities.feature_vector_response import FeatureVectorResponse
from ..entities.sensor import Sensor
from ..settings import get_settings


class FeatureEndpoint:
    def __init__(self, client: APIClient, featurizer: Featurizer) -> None:
        self.client = client
        self.featurizer = featurizer

    def _fetch_measurements(self, start: int, end: int, sensor_id: Optional[str]) -> List[Sensor]:
        if sensor_id:
            payload = self.client.get_sensor_measurements(sensor_id, start=start, end=end)
            data_key = "requestData" if isinstance(payload, dict) and "requestData" in payload else "responseData"
        else:
            payload = self.client.get_all_measurements(start=start, end=end)
            data_key = "responseData"
        return flatten_measurements(payload, data_key=data_key)

    def compute_vectors(self, start: int, end: int, sensor_id: Optional[str]) -> List[FeatureVectorResponse]:
        sensors = self._fetch_measurements(start, end, sensor_id)
        if not sensors:
            raise HTTPException(status_code=404, detail="No measurements found for the requested window")

        vectors = self.featurizer.extract_features(sensors)
        if sensor_id:
            vectors = [vector for vector in vectors if vector.sensor_id == sensor_id]
        if not vectors:
            raise HTTPException(status_code=404, detail="Unable to build feature vectors for the requested sensors")
        return [FeatureVectorResponse.from_model(vector) for vector in vectors]


router = APIRouter()
settings = get_settings()
endpoint = FeatureEndpoint(client=APIClient(), featurizer=Featurizer())


@router.get("/feature-vectors", response_model=List[FeatureVectorResponse])
def get_feature_vectors(
    start: Optional[int] = Query(None, description="Window start timestamp (epoch seconds)"),
    end: Optional[int] = Query(None, description="Window end timestamp (epoch seconds)"),
    sensor_id: Optional[str] = Query(None, description="Optional sensor ID filter"),
):
    now = int(datetime.now(tz=timezone.utc).timestamp())
    window_end = end or now
    default_window_seconds = settings.default_time_window_hours * 60 * 60
    window_start = start or (window_end - default_window_seconds)

    if window_start >= window_end:
        raise HTTPException(status_code=400, detail="start must be before end")
    return endpoint.compute_vectors(start=window_start, end=window_end, sensor_id=sensor_id)
