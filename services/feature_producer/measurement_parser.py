from typing import Dict, Any, List, Sequence, Union
from ..entities.sensor import Sensor

PayloadType = Union[Dict[str, Any], Sequence[Dict[str, Any]]]

def flatten_measurements(payload: PayloadType, data_key: str = "responseData") -> List[Sensor]:
    sensors: List[Sensor] = []
    if isinstance(payload, dict):
        blocks = payload.get(data_key, [])
    else:
        blocks = payload

    for block in blocks:
        sensor_id = block.get("sensorId")
        if not sensor_id:
            continue
        for measurement in block.get("measurements", []):
            item = dict(measurement)
            item["sensorId"] = sensor_id
            sensors.append(Sensor.model_validate(item))
    return sensors