import requests
from typing import List, Optional, Dict, Any
from datetime import datetime


class APIClient:
    def __init__(self, base_url: str = "https://hm-sense-open-data-api.kube.cs.hm.edu/api") -> None:
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code}: {e.response.text}") from e
        except requests.exceptions.RequestException as e:
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
        format: str = "json"
    ) -> Dict[str, Any]:
        params = {"start": str(start), "end": str(end), "format": format}
        return self._make_request("/roomclimate/measurements/all", params)
    
    def get_all_measurements_by_type(
        self,
        sensor_type: str,
        start: int,
        end: int,
        format: str = "json"
    ) -> Dict[str, Any]:
        params = {"start": str(start), "end": str(end), "format": format}
        return self._make_request(f"/roomclimate/measurements/all/{sensor_type}", params)
    
    def get_sensor_measurements(
        self,
        sensor_id: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        params = {"format": format}
        if start is not None:
            params["start"] = str(start)
        if end is not None:
            params["end"] = str(end)
        return self._make_request(f"/roomclimate/measurements/{sensor_id}", params)
    
    def get_sensor_measurements_by_type(
        self,
        sensor_id: str,
        sensor_type: str,
        start: Optional[int] = None,
        end: Optional[int] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        params = {"format": format}
        if start is not None:
            params["start"] = str(start)
        if end is not None:
            params["end"] = str(end)
        return self._make_request(f"/roomclimate/measurements/{sensor_id}/{sensor_type}", params)
    
    def get_metadata(self) -> str:
        url = f"{self.base_url}/metadata"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
        
    