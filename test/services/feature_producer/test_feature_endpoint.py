import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from services.feature_producer.feature_endpoint import FeatureEndpoint
from services.feature_producer.featurizer import Featurizer


def iso_ts(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def build_payload() -> dict:
    base = int(datetime(2024, 5, 1, tzinfo=timezone.utc).timestamp())
    series_one = [
        {"timestamp": iso_ts(base + offset), "humidity": 30 + idx, "temperature": 20.0 + idx * 0.1,
         "co2": 600 + idx * 5, "motion": float(idx % 2), "light": 150.0}
        for idx, offset in enumerate(range(0, 3600, 300))
    ]
    series_two = [
        {"timestamp": iso_ts(base + offset), "humidity": 35.0, "temperature": 21.0,
         "co2": 650 + idx * 3, "motion": 0.0, "light": 0.0}
        for idx, offset in enumerate(range(0, 3600, 300))
    ]
    response_payload = {
        "responseData": [
            {"sensorId": "sensor81", "measurements": series_one},
            {"sensorId": "sensor82", "measurements": series_two},
        ]
    }
    request_payload = {
        "requestData": [
            {"sensorId": "sensor81", "measurements": series_one},
        ]
    }
    return {"response": response_payload, "request": request_payload, "start": base, "end": base + 3600}


class FakeAPIClient:
    def __init__(self, response_payload: dict, request_payload: dict):
        self._response_payload = response_payload
        self._request_payload = request_payload

    def get_all_measurements(self, *_, **__):
        return self._response_payload

    def get_sensor_measurements(self, *_, **__):
        return self._request_payload


class FeatureEndpointTests(unittest.TestCase):
    def setUp(self):
        payload = build_payload()
        self.start = payload["start"]
        self.end = payload["end"]
        client = FakeAPIClient(payload["response"], payload["request"])
        self.endpoint = FeatureEndpoint(client=client, featurizer=Featurizer())

    def test_compute_vectors_returns_all_sensors(self):
        result = self.endpoint.compute_vectors(start=self.start, end=self.end, sensor_id=None)
        sensor_ids = {vector.sensor_id for vector in result}
        self.assertEqual(sensor_ids, {"sensor81", "sensor82"})

    def test_compute_vectors_filters_single_sensor(self):
        result = self.endpoint.compute_vectors(start=self.start, end=self.end, sensor_id="sensor81")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].sensor_id, "sensor81")


if __name__ == "__main__":
    unittest.main()
