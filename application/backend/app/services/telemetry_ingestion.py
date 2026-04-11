"""
Telemetry validation, normalization, broker publish, Influx write (optional).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.constants import TOPIC_TELEMETRY_NORMALIZED, TOPIC_TELEMETRY_RAW
from app.broker.factory import get_broker

logger = logging.getLogger(__name__)


def validate_telemetry(raw: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    if "machine_id" not in raw:
        return False, "missing machine_id", {}
    try:
        ts = raw.get("timestamp")
        if ts is None:
            ts = datetime.now(timezone.utc).isoformat()
        normalized = {
            "machine_id": str(raw["machine_id"]),
            "timestamp": ts,
            "position": {
                "x": float(raw.get("position", {}).get("x", 0)),
                "y": float(raw.get("position", {}).get("y", 0)),
                "z": float(raw.get("position", {}).get("z", 0)),
            },
            "speed_m_s": float(raw.get("speed_m_s", 0)),
            "fuel_l": float(raw.get("fuel_l", 0)),
            "payload_t": float(raw.get("payload_t", 0)),
            "wear_index": float(raw.get("wear_index", 0)),
            "event_type": raw.get("event_type", "periodic"),
            "meta": raw.get("meta") or {},
        }
        return True, "", normalized
    except (TypeError, ValueError) as e:
        return False, str(e), {}


async def ingest_telemetry(raw: dict[str, Any], influx_writer: Any | None) -> dict[str, Any]:
    ok, err, norm = validate_telemetry(raw)
    if not ok:
        return {"accepted": False, "error": err}

    broker = get_broker()
    if broker and broker.is_connected:
        await broker.publish(TOPIC_TELEMETRY_RAW, raw)
        await broker.publish(TOPIC_TELEMETRY_NORMALIZED, norm)

    if influx_writer:
        try:
            influx_writer.write_point(norm)
        except Exception as e:
            logger.warning("Influx write failed (offline OK): %s", e)

    return {"accepted": True, "normalized": norm}
