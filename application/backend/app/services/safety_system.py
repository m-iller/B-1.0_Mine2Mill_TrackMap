"""
Real-time safety rules: speed, braking, proximity, zones, overload.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.constants import ALERT_CRITICAL, ALERT_EMERGENCY, ALERT_WARNING


@dataclass
class SafetyAlert:
    level: str
    code: str
    machine_id: str | None
    detail: dict[str, Any]


class OperatorSafetySystem:
    def __init__(self) -> None:
        self.speed_limit_m_s = 12.0
        self.proximity_m = 25.0
        self.harsh_brake_m_s2 = 6.0
        self.overload_t = 290.0

    def evaluate_telemetry(self, sample: dict[str, Any]) -> list[SafetyAlert]:
        alerts: list[SafetyAlert] = []
        mid = sample.get("machine_id")
        spd = float(sample.get("speed_m_s", 0))
        if spd > self.speed_limit_m_s:
            lvl = ALERT_CRITICAL if spd > self.speed_limit_m_s * 1.2 else ALERT_WARNING
            alerts.append(SafetyAlert(lvl, "over_speed", mid, {"speed_m_s": spd}))

        decel = float(sample.get("longitudinal_accel_m_s2", 0))
        if decel < -self.harsh_brake_m_s2:
            alerts.append(
                SafetyAlert(ALERT_WARNING, "harsh_braking", mid, {"decel_m_s2": decel})
            )

        load_t = float(sample.get("payload_t", 0))
        if load_t > self.overload_t:
            alerts.append(
                SafetyAlert(ALERT_CRITICAL, "mechanical_overload", mid, {"payload_t": load_t})
            )

        if sample.get("in_restricted_zone"):
            alerts.append(
                SafetyAlert(ALERT_EMERGENCY, "restricted_zone_entry", mid, {"zone": sample.get("zone_id")})
            )
        return alerts

    def proximity_scan(self, machines: list[dict[str, Any]], cell_meters: float = 10.0) -> list[SafetyAlert]:
        alerts: list[SafetyAlert] = []
        n = len(machines)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = machines[i], machines[j]
                pa = a.get("position", {})
                pb = b.get("position", {})
                dist = math.hypot(
                    float(pa.get("x", 0)) - float(pb.get("x", 0)),
                    float(pa.get("y", 0)) - float(pb.get("y", 0)),
                ) * cell_meters
                if dist < self.proximity_m and dist > 0:
                    lvl = ALERT_CRITICAL if dist < self.proximity_m * 0.4 else ALERT_WARNING
                    alerts.append(
                        SafetyAlert(
                            lvl,
                            "unsafe_proximity",
                            None,
                            {"a": a.get("id"), "b": b.get("id"), "dist_m": dist},
                        )
                    )
        return alerts

    def to_incident_dict(self, a: SafetyAlert) -> dict[str, Any]:
        return {"severity": a.level, "category": a.code, "detail": a.detail, "machine_id": a.machine_id}
