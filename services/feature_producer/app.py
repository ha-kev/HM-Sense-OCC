from fastapi import FastAPI

from .feature_endpoint import router as feature_router

app = FastAPI(title="Feature Producer Service", version="1.0.0")
app.include_router(feature_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
