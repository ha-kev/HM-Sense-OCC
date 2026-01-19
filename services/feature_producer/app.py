import logging

from fastapi import FastAPI

from .feature_endpoint import router as feature_router
from ..settings import get_settings

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("Starting Feature Producer Service with log level: %s", settings.log_level)

app = FastAPI(title="Feature Producer Service", version="1.0.0")
app.include_router(feature_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
