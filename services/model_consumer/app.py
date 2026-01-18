from fastapi import FastAPI

from .prediction_endpoint import router as prediction_router

app = FastAPI(title="HM Sense Prediction Service")
app.include_router(prediction_router, prefix="/api")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
