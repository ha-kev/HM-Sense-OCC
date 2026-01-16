import json
import zlib
from typing import Union
from ..entities.sensor import Sensor

class SensorSerializer:
    def __init__(self, compress: bool = False):
        self.compress = compress

    def serialize(self, sensor: Sensor) -> bytes:
        json_str = sensor.model_dump_json(by_alias=True)
        raw = json_str.encode("utf-8")
        return zlib.compress(raw) if self.compress else raw

    def deserialize(self, payload: Union[bytes, str, dict]) -> Sensor:
        if isinstance(payload, dict):
            return Sensor.model_validate(payload)
        
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        
        raw = zlib.decompress(payload) if self.compress else payload
        raw_bytes: bytes = bytes(raw)
        data = json.loads(raw_bytes.decode("utf-8"))
        return Sensor.model_validate(data)