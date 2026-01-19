import logging

from fastapi import FastAPI

from .prediction_endpoint import router as prediction_router
from ..settings import get_settings

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("Starting HM Sense Prediction Service with log level: %s", settings.log_level)

app = FastAPI(title="HM Sense Prediction Service")
app.include_router(prediction_router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
