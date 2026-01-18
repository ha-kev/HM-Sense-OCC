import logging
import time

import requests
from typing import List, Optional, Dict, Any

from ..settings import Settings, get_settings

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        request_timeout: Optional[int] = None,
        default_format: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.base_url = base_url or self.settings.api_base_url
        self.request_timeout = request_timeout or self.settings.api_request_timeout_seconds
        self.default_format = default_format or self.settings.default_measurement_format
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        logger.info(
            "APIClient initialized base_url=%s timeout=%ss format=%s",
            self.base_url,
            self.request_timeout,
            self.default_format,
        )
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        start_time = time.perf_counter()
        logger.debug("Requesting %s params=%s", url, params)
        try:
            response = self.session.get(url, params=params, timeout=self.request_timeout)
            response.raise_for_status()
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Successful response %s status=%s duration=%.2fms",
                url,
                response.status_code,
                duration_ms,
            )
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error for %s status=%s", url, e.response.status_code)
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}") from e
        except requests.exceptions.RequestException as e:
            logger.error("Request failure for %s: %s", url, e)
            raise RuntimeError(f"API request failed: {str(e)}") from e
    
    def get_sensors(self) -> List[str]:
        response = self._make_request("/roomclimate/sensors")
        # API returns array of sensor IDs
        if isinstance(response, list):
            return response
        return []
    
    def get_all_measurements(
        self, 
        start: int, 
        end: int, 
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"start": str(start), "end": str(end), "format": format or self.default_format}
        logger.debug("Fetching all measurements start=%s end=%s format=%s", start, end, params["format"])
        return self._make_request("/roomclimate/measurements/all", params)
    
    def get_all_measurements_by_type(
        self,
        sensor_type: str,
        start: int,
        end: int,
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"start": str(start), "end": str(end), "format": format or self.default_format}
        logger.debug(
            "Fetching measurements by type sensor_type=%s start=%s end=%s format=%s",
            sensor_type,
            start,
            end,
            params["format"],
        )
        return self._make_request(f"/roomclimate/measurements/all/{sensor_type}", params)
    
    def get_sensor_measurements(
        self,
        sensor_id: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"format": format or self.default_format}
        if start is not None:
            params["start"] = str(start)
        if end is not None:
            params["end"] = str(end)
        logger.debug(
            "Fetching sensor measurements sensor_id=%s start=%s end=%s format=%s",
            sensor_id,
            params.get("start"),
            params.get("end"),
            params["format"],
        )
        return self._make_request(f"/roomclimate/measurements/{sensor_id}", params)
    
    def get_sensor_measurements_by_type(
        self,
        sensor_id: str,
        sensor_type: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
        format: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"format": format or self.default_format}
        if start is not None:
            params["start"] = str(start)
        if end is not None:
            params["end"] = str(end)
        logger.debug(
            "Fetching sensor measurements by type sensor_id=%s type=%s start=%s end=%s format=%s",
            sensor_id,
            sensor_type,
            params.get("start"),
            params.get("end"),
            params["format"],
        )
        return self._make_request(f"/roomclimate/measurements/{sensor_id}/{sensor_type}", params)
    
    def get_metadata(self) -> str:
        url = f"{self.base_url}/metadata"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
        
    