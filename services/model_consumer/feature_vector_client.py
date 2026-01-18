import logging
from datetime import datetime, timezone
from typing import List, Optional

import requests

from ..entities.feature_vector_response import FeatureVectorResponse
from ..entities.feature_vectors_result import FeatureVectorsResult
from ..entities.sensor import Sensor
from ..settings import Settings, get_settings

logger = logging.getLogger(__name__)


class FeatureVectorClient:
    """Fetches feature vectors from the FastAPI feature endpoint."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        request_timeout: Optional[int] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        base = base_url or self.settings.feature_endpoint_base_url
        self.base_url = base.rstrip("/")
        self.request_timeout = request_timeout or self.settings.feature_endpoint_timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        logger.info(
            "FeatureVectorClient initialized base_url=%s timeout=%ss",
            self.base_url,
            self.request_timeout,
        )

    def fetch_feature_vectors(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        sensor_id: Optional[str] = None,
    ) -> FeatureVectorsResult:
        params = {}
        if start is not None:
            params["start"] = str(start)
        if end is not None:
            params["end"] = str(end)
        if sensor_id:
            params["sensor_id"] = sensor_id

        url = f"{self.base_url}/feature-vectors"
        logger.info(
            "Fetching feature vectors url=%s sensor_id=%s start=%s end=%s",
            url,
            sensor_id or "*",
            params.get("start"),
            params.get("end"),
        )
        try:
            response = self.session.get(url, params=params or None, timeout=self.request_timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.HTTPError as exc:
            logger.error("Feature endpoint returned HTTP %s", exc.response.status_code if exc.response else "?")
            detail = exc.response.text if exc.response is not None else str(exc)
            raise RuntimeError(f"Feature endpoint error: {detail}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to reach feature endpoint: %s", exc)
            raise RuntimeError(f"Feature endpoint request failed: {exc}") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("Unexpected feature endpoint payload; expected object")

        vectors_raw = payload.get("feature_vectors")
        sensors_raw = payload.get("current_sensors")
        if not isinstance(vectors_raw, list) or not isinstance(sensors_raw, list):
            raise RuntimeError("Invalid feature endpoint payload structure")

        vectors: List[FeatureVectorResponse] = [FeatureVectorResponse(**item) for item in vectors_raw]
        sensor_models: List[Sensor] = [Sensor(**item) for item in sensors_raw]
        logger.debug(
            "Received %s feature vectors and %s sensor snapshots",
            len(vectors),
            len(sensor_models),
        )
        return FeatureVectorsResult(feature_vectors=vectors, current_sensors=sensor_models)

    def fetch_recent_window(
        self,
        window_hours: int,
        sensor_id: Optional[str] = None,
        end: Optional[int] = None,
    ) -> FeatureVectorsResult:
        now = end or int(datetime.now(tz=timezone.utc).timestamp())
        start = now - int(window_hours * 60 * 60)
        return self.fetch_feature_vectors(start=start, end=now, sensor_id=sensor_id)
