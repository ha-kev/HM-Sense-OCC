import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..entities.prediction_response import PredictionResponse
from ..entities.prediction_result import PredictionResult
from ..settings import get_settings
from .feature_vector_client import FeatureVectorClient
from .model_consumer import HMMPredictor

logger = logging.getLogger(__name__)


class PredictionEndpoint:
    def __init__(self, client: FeatureVectorClient, predictor: HMMPredictor) -> None:
        self.client = client
        self.predictor = predictor
        logger.info("PredictionEndpoint initialized")

    def compute_predictions(self, start: int, end: int, sensor_id: Optional[str]) -> PredictionResult:
        logger.info(
            "Computing predictions sensor_id=%s window_start=%s window_end=%s",
            sensor_id or "*",
            start,
            end,
        )
        if start >= end:
            logger.warning("Rejected prediction request with invalid window start=%s end=%s", start, end)
            raise HTTPException(status_code=400, detail="start must be before end")

        try:
            vector_bundle = self.client.fetch_feature_vectors(start=start, end=end, sensor_id=sensor_id)
        except RuntimeError as exc:
            logger.exception("Failed to fetch feature vectors from producer")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        vectors = vector_bundle.feature_vectors
        if not vectors:
            raise HTTPException(status_code=404, detail="No feature vectors available for the requested window")

        predictions: List[PredictionResponse] = []
        for vector in vectors:
            try:
                feature_dict = self._vector_to_dict(vector)
                result = self.predictor.predict(feature_dict)
            except ValueError as exc:
                logger.error("Unable to score vector sensor_id=%s: %s", vector.sensor_id, exc)
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except RuntimeError as exc:
                logger.exception("Model artifacts unavailable for prediction")
                raise HTTPException(status_code=500, detail=str(exc)) from exc

            predictions.append(
                PredictionResponse(
                    sensor_id=vector.sensor_id,
                    state=result["state"],
                    state_label=result["state_label"],
                    state_probabilities=result["state_probabilities"],
                )
            )

        return PredictionResult(predictions=predictions, current_sensors=vector_bundle.current_sensors)

    @staticmethod
    def _vector_to_dict(vector: Any) -> Dict[str, float]:
        dump = getattr(vector, "model_dump", None)
        if callable(dump):
            return dump()
        if hasattr(vector, "dict"):
            return vector.dict()
        raise ValueError("Unsupported feature vector instance")


router = APIRouter()
settings = get_settings()
endpoint = PredictionEndpoint(client=FeatureVectorClient(), predictor=HMMPredictor())


@router.get("/predictions", response_model=PredictionResult, response_model_by_alias=False)
def get_predictions(
    start: Optional[int] = Query(None, description="Window start timestamp (epoch seconds)"),
    end: Optional[int] = Query(None, description="Window end timestamp (epoch seconds)"),
    sensor_id: Optional[str] = Query(None, description="Optional sensor ID filter"),
):
    logger.info(
        "GET /predictions start=%s end=%s sensor_id=%s",
        start,
        end,
        sensor_id,
    )
    now = int(datetime.now(tz=timezone.utc).timestamp())
    window_end = end or now
    default_window_seconds = settings.default_time_window_hours * 60 * 60
    window_start = start or (window_end - default_window_seconds)

    return endpoint.compute_predictions(start=window_start, end=window_end, sensor_id=sensor_id)
