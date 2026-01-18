import logging
from typing import Dict, List, Optional

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from .api_client import APIClient
from .featurizer import Featurizer
from .measurement_parser import flatten_measurements
from ..entities.feature_vector_response import FeatureVectorResponse
from ..entities.feature_vectors_result import FeatureVectorsResult
from ..entities.sensor import Sensor
from ..settings import get_settings

logger = logging.getLogger(__name__)


class FeatureEndpoint:
    def __init__(self, client: APIClient, featurizer: Featurizer) -> None:
        self.client = client
        self.featurizer = featurizer
        logger.info("FeatureEndpoint initialized")

    def _fetch_measurements(self, start: int, end: int, sensor_id: Optional[str]) -> List[Sensor]:
        if sensor_id:
            payload = self.client.get_sensor_measurements(sensor_id, start=start, end=end)
            data_key = "requestData" if isinstance(payload, dict) and "requestData" in payload else "responseData"
        else:
            payload = self.client.get_all_measurements(start=start, end=end)
            data_key = "responseData"
        sensors = flatten_measurements(payload, data_key=data_key)
        logger.debug(
            "Fetched %s normalized measurements (sensor_id=%s start=%s end=%s)",
            len(sensors),
            sensor_id or "*",
            start,
            end,
        )
        return sensors

    def compute_vectors(self, start: int, end: int, sensor_id: Optional[str]) -> FeatureVectorsResult:
        logger.info(
            "Computing feature vectors sensor_id=%s window_start=%s window_end=%s",
            sensor_id or "*",
            start,
            end,
        )
        sensors = self._fetch_measurements(start, end, sensor_id)
        if not sensors:
            raise HTTPException(status_code=404, detail="No measurements found for the requested window")

        vectors = self.featurizer.extract_features(sensors)
        if sensor_id:
            vectors = [vector for vector in vectors if vector.sensor_id == sensor_id]
        if not vectors:
            raise HTTPException(status_code=404, detail="Unable to build feature vectors for the requested sensors")
        feature_vectors = [FeatureVectorResponse.from_model(vector) for vector in vectors]
        current_sensors = self._latest_measurements(sensors, sensor_id)
        return FeatureVectorsResult(feature_vectors=feature_vectors, current_sensors=current_sensors)

    @staticmethod
    def _latest_measurements(sensors: List[Sensor], sensor_id: Optional[str]) -> List[Sensor]:
        latest: Dict[str, Sensor] = {}
        for sensor in sensors:
            current = latest.get(sensor.sensor_id)
            if current is None or sensor.timestamp > current.timestamp:
                latest[sensor.sensor_id] = sensor
        if sensor_id:
            selected = latest.get(sensor_id)
            return [selected] if selected else []
        return list(latest.values())


router = APIRouter()
settings = get_settings()
endpoint = FeatureEndpoint(client=APIClient(), featurizer=Featurizer())


@router.get("/feature-vectors", response_model=FeatureVectorsResult, response_model_by_alias=False)
def get_feature_vectors(
    start: Optional[int] = Query(None, description="Window start timestamp (epoch seconds)"),
    end: Optional[int] = Query(None, description="Window end timestamp (epoch seconds)"),
    sensor_id: Optional[str] = Query(None, description="Optional sensor ID filter"),
):
    logger.info(
        "GET /feature-vectors start=%s end=%s sensor_id=%s",
        start,
        end,
        sensor_id,
    )
    now = int(datetime.now(tz=timezone.utc).timestamp())
    window_end = end or now
    default_window_seconds = settings.default_time_window_hours * 60 * 60
    window_start = start or (window_end - default_window_seconds)

    if window_start >= window_end:
        logger.warning("Rejected request due to invalid window start=%s end=%s", window_start, window_end)
        raise HTTPException(status_code=400, detail="start must be before end")
    return endpoint.compute_vectors(start=window_start, end=window_end, sensor_id=sensor_id)
