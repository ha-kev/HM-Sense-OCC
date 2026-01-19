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
        logger.debug("Starting measurement fetch for sensor_id=%s, start=%s, end=%s", sensor_id or "*", start, end)
        try:
            if sensor_id:
                logger.debug("Fetching measurements for specific sensor: %s", sensor_id)
                payload = self.client.get_sensor_measurements(sensor_id, start=start, end=end)
                data_key = "requestData" if isinstance(payload, dict) and "requestData" in payload else "responseData"
                logger.debug("Received payload for sensor %s, using data_key: %s", sensor_id, data_key)
            else:
                logger.debug("Fetching all measurements")
                payload = self.client.get_all_measurements(start=start, end=end)
                data_key = "responseData"
                logger.debug("Received payload for all sensors, using data_key: %s", data_key)
        except Exception as exc:
            logger.error("Failed to fetch measurements from API (sensor_id=%s, start=%s, end=%s): %s", 
                        sensor_id or "*", start, end, str(exc))
            logger.warning("API appears to be unreachable or returned an error. Check network connectivity and API status.")
            raise HTTPException(status_code=502, detail=f"Failed to fetch measurements from external API: {str(exc)}") from exc
        
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
        logger.debug("Fetched %d sensors for processing", len(sensors))
        if not sensors:
            logger.warning("No measurements found for the requested window (sensor_id=%s, start=%s, end=%s)", sensor_id or "*", start, end)
            raise HTTPException(status_code=404, detail="No measurements found for the requested window")

        logger.debug("Extracting features from %d sensors", len(sensors))
        vectors = self.featurizer.extract_features(sensors)
        logger.debug("Extracted %d raw feature vectors", len(vectors))
        if sensor_id:
            logger.debug("Filtering vectors for sensor_id: %s", sensor_id)
            vectors = [vector for vector in vectors if vector.sensor_id == sensor_id]
            logger.debug("After filtering: %d vectors for sensor %s", len(vectors), sensor_id)
        if not vectors:
            logger.warning("Unable to build feature vectors for the requested sensors (sensor_id=%s)", sensor_id or "*")
            raise HTTPException(status_code=404, detail="Unable to build feature vectors for the requested sensors")
        logger.debug("Converting %d vectors to response format", len(vectors))
        feature_vectors = [FeatureVectorResponse.from_model(vector) for vector in vectors]
        logger.debug("Converted to %d feature vector responses", len(feature_vectors))
        current_sensors = self._latest_measurements(sensors, sensor_id)
        logger.debug("Identified %d current sensors", len(current_sensors))
        result = FeatureVectorsResult(feature_vectors=feature_vectors, current_sensors=current_sensors)
        logger.info("Successfully computed %d feature vectors for sensor_id=%s", len(feature_vectors), sensor_id or "*")
        return result

    @staticmethod
    def _latest_measurements(sensors: List[Sensor], sensor_id: Optional[str]) -> List[Sensor]:
        logger.debug("Finding latest measurements from %d sensors (sensor_id filter: %s)", len(sensors), sensor_id or "*")
        latest: Dict[str, Sensor] = {}
        for sensor in sensors:
            current = latest.get(sensor.sensor_id)
            if current is None or sensor.timestamp > current.timestamp:
                latest[sensor.sensor_id] = sensor
        logger.debug("Found latest measurements for %d unique sensors", len(latest))
        if sensor_id:
            selected = latest.get(sensor_id)
            result = [selected] if selected else []
            logger.debug("Filtered for sensor_id %s: %d sensors returned", sensor_id, len(result))
            return result
        result = list(latest.values())
        logger.debug("Returning all latest sensors: %d", len(result))
        return result


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
    logger.debug("Current timestamp: %s", now)
    window_end = end or now
    default_window_seconds = settings.default_time_window_hours * 60 * 60
    window_start = start or (window_end - default_window_seconds)
    logger.debug("Calculated window: start=%s, end=%s (default_window_hours=%s)", window_start, window_end, settings.default_time_window_hours)

    if window_start >= window_end:
        logger.warning("Rejected request due to invalid window start=%s end=%s", window_start, window_end)
        raise HTTPException(status_code=400, detail="start must be before end")
    logger.debug("Calling compute_vectors with start=%s, end=%s, sensor_id=%s", window_start, window_end, sensor_id)
    return endpoint.compute_vectors(start=window_start, end=window_end, sensor_id=sensor_id)
