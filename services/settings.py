from functools import lru_cache
from pydantic import Field

try:  # Pydantic v2
    from pydantic_settings import BaseSettings
except ImportError:  # Pydantic v1 fallback
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration for the services package."""

    api_base_url: str = Field(
        "https://hm-sense-open-data-api.kube.cs.hm.edu/api",
        description="Base URL for the external HM Sense API",
    )
    api_request_timeout_seconds: int = Field(
        30,
        ge=1,
        description="HTTP timeout in seconds when calling the HM Sense API",
    )
    default_time_window_hours: int = Field(
        3,
        ge=1,
        description="Default number of hours to look back when no window is provided",
    )
    default_measurement_format: str = Field(
        "json",
        description="Format parameter forwarded to the HM Sense API",
    )
    feature_endpoint_base_url: str = Field(
        "http://0.0.0.0:8000/api",
        description="Base URL for the local feature endpoint API",
    )
    feature_endpoint_timeout_seconds: int = Field(
        10,
        ge=1,
        description="HTTP timeout in seconds for feature endpoint calls",
    )

    class Config:
        env_file = ".env"
        env_prefix = "FEATURE_PRODUCER_"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance to avoid repeated env parsing."""
    return Settings()
