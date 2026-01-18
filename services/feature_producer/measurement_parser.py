import logging
from typing import Dict, Any, List, Sequence, Union

from ..entities.sensor import Sensor

PayloadType = Union[Dict[str, Any], Sequence[Dict[str, Any]]]

logger = logging.getLogger(__name__)

def _build_sensor(payload: Dict[str, Any]) -> Sensor:
    validator = getattr(Sensor, "model_validate", None)
    if callable(validator):
        return validator(payload)
    return Sensor(**payload)


def flatten_measurements(payload: PayloadType, data_key: str = "responseData") -> List[Sensor]:
    sensors: List[Sensor] = []
    if isinstance(payload, dict):
        blocks = payload.get(data_key, [])
        logger.debug(
            "Flattening payload dict with keys=%s data_key=%s block_count=%s",
            list(payload.keys()),
            data_key,
            len(blocks) if hasattr(blocks, "__len__") else "unknown",
        )
    else:
        blocks = payload
        logger.debug(
            "Flattening payload sequence length=%s data_key=%s",
            len(blocks) if hasattr(blocks, "__len__") else "unknown",
            data_key,
        )

    for block in blocks:
        if not isinstance(block, dict):
            logger.warning("Skipping non-dict measurement block of type %s", type(block).__name__)
            continue
        sensor_id = block.get("sensorId")
        if not sensor_id:
            logger.warning("Skipping block without sensorId: %s", block)
            continue
        for measurement in block.get("measurements", []):
            item = dict(measurement)
            item["sensorId"] = sensor_id
            sensors.append(_build_sensor(item))
    sensor_ids = {s.sensor_id for s in sensors}
    logger.info("Flattened %s measurements for %s sensors", len(sensors), len(sensor_ids))
    return sensors