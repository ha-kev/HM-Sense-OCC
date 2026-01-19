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

        logger.debug("Fetching feature vectors from producer for start=%s, end=%s, sensor_id=%s", start, end, sensor_id)
        try:
            vector_bundle = self.client.fetch_feature_vectors(start=start, end=end, sensor_id=sensor_id)
            logger.debug("Successfully fetched feature vector bundle with %d vectors and %d current sensors", 
                        len(vector_bundle.feature_vectors), len(vector_bundle.current_sensors))
        except RuntimeError as exc:
            logger.exception("Failed to fetch feature vectors from producer")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        vectors = vector_bundle.feature_vectors
        logger.debug("Processing %d feature vectors for predictions", len(vectors))
        if not vectors:
            logger.warning("No feature vectors available for the requested window (start=%s, end=%s, sensor_id=%s)", start, end, sensor_id or "*")
            raise HTTPException(status_code=404, detail="No feature vectors available for the requested window")

        predictions: List[PredictionResponse] = []
        logger.debug("Starting prediction loop for %d vectors", len(vectors))
        for i, vector in enumerate(vectors):
            logger.debug("Processing vector %d/%d for sensor_id=%s", i+1, len(vectors), vector.sensor_id)
            try:
                feature_dict = self._vector_to_dict(vector)
                logger.debug("Converted vector to dict with %d features", len(feature_dict))
                result = self.predictor.predict(feature_dict)
                logger.debug("Prediction result for sensor %s: state=%s, label=%s", vector.sensor_id, result["state"], result["state_label"])
            except ValueError as exc:
                logger.error("Unable to score vector sensor_id=%s: %s", vector.sensor_id, exc)
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except RuntimeError as exc:
                logger.exception("Model artifacts unavailable for prediction on sensor %s", vector.sensor_id)
                raise HTTPException(status_code=500, detail=str(exc)) from exc

            prediction = PredictionResponse(
                sensor_id=vector.sensor_id,
                state=result["state"],
                state_label=result["state_label"],
                state_probabilities=result["state_probabilities"],
            )
            predictions.append(prediction)
            logger.debug("Added prediction for sensor %s", vector.sensor_id)

        result = PredictionResult(predictions=predictions, current_sensors=vector_bundle.current_sensors)
        logger.info("Successfully computed %d predictions for sensor_id=%s", len(predictions), sensor_id or "*")
        return result

    @staticmethod
    def _vector_to_dict(vector: Any) -> Dict[str, float]:
        logger.debug("Converting feature vector to dict, vector type: %s", type(vector).__name__)
        dump = getattr(vector, "model_dump", None)
        if callable(dump):
            logger.debug("Using model_dump() method for conversion")
            return dump()
        if hasattr(vector, "dict"):
            logger.debug("Using dict() method for conversion")
            return vector.dict()
        logger.error("Unsupported feature vector instance type: %s", type(vector).__name__)
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
    logger.debug("Current timestamp: %s", now)
    window_end = end or now
    default_window_seconds = settings.default_time_window_hours * 60 * 60
    window_start = start or (window_end - default_window_seconds)
    logger.debug("Calculated window: start=%s, end=%s (default_window_hours=%s)", window_start, window_end, settings.default_time_window_hours)

    logger.debug("Calling compute_predictions with start=%s, end=%s, sensor_id=%s", window_start, window_end, sensor_id)
    return endpoint.compute_predictions(start=window_start, end=window_end, sensor_id=sensor_id)
