"""
Synthetic mining telemetry + machine lifecycles: movement, fuel, wear, failures, operator variance.
"""

from __future__ import annotations

import math
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd


class SyntheticMiningDataGenerator:
    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

    def machine_track(
        self,
        steps: int = 500,
        cell_m: float = 10.0,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        mid = str(uuid.uuid4())
        x, y = 10.0, 10.0
        t0 = datetime.now(timezone.utc)
        wear = 0.0
        fuel = 800.0
        status = "moving"
        for i in range(steps):
            noise = self.np_rng.normal(0, 0.08, size=2)
            heading = 2 * math.pi * i / 97.0 + noise[0]
            spd = max(0.0, 6 + 2 * math.sin(i / 15.0) + noise[1])
            x += math.cos(heading) * spd * 0.2
            y += math.sin(heading) * spd * 0.2
            fuel -= 0.04 * spd
            wear += 0.0002 * spd + abs(noise[1]) * 1e-4
            if self.rng.random() < 0.002:
                status = "failure"
            elif status == "failure" and self.rng.random() < 0.2:
                status = "moving"
            payload = max(0.0, 180 + self.np_rng.normal(0, 12)) if status != "failure" else 0.0
            event = "periodic" if i % 5 else "heartbeat"
            if status == "failure":
                event = "alert"
            sample = {
                "machine_id": mid,
                "timestamp": (t0 + timedelta(seconds=i * 12)).isoformat(),
                "position": {"x": float(x), "y": float(y), "z": float(10 + 0.01 * (x + y))},
                "speed_m_s": float(spd),
                "fuel_l": float(fuel),
                "payload_t": float(payload),
                "wear_index": float(wear),
                "event_type": event,
                "longitudinal_accel_m_s2": float(self.np_rng.normal(-0.2, 1.2)),
                "meta": {"cell_m": cell_m, "synthetic": True},
            }
            out.append(sample)
        return out

    def training_frame(self, n: int = 400) -> pd.DataFrame:
        hours = self.np_rng.uniform(10, 800, n)
        wear_mm = self.np_rng.uniform(0.5, 40, n)
        ttf_h = np.maximum(5, 800 - hours * 0.4 - wear_mm * 2 + self.np_rng.normal(0, 20, n))
        tonnes = self.np_rng.uniform(200, 9000, n)
        fuel_l = tonnes * self.np_rng.uniform(0.15, 0.45, n) * (1 + wear_mm / 100)
        grade = self.np_rng.uniform(0, 12, n)
        active = self.np_rng.integers(3, 25, n)
        hardness = self.np_rng.uniform(0.3, 1.0, n)
        flow_tph = active * 35 * hardness + self.np_rng.normal(0, 15, n)
        speed_std = self.np_rng.uniform(0.5, 4.0, n)
        brake = self.np_rng.poisson(3, n)
        idle = self.np_rng.uniform(0.05, 0.35, n)
        vib = self.np_rng.uniform(0.1, 8.0, n)
        temp = self.np_rng.uniform(60, 105, n)
        press = self.np_rng.uniform(180, 320, n)
        haul = self.np_rng.uniform(20, 120, n)
        fe = self.np_rng.uniform(0.2, 0.55, n)
        safety = self.np_rng.uniform(0.5, 1.0, n)
        return pd.DataFrame(
            {
                "hours": hours,
                "wear_mm": wear_mm,
                "ttf_h": ttf_h,
                "fuel_l": fuel_l,
                "tonnes_moved": tonnes,
                "grade_pct": grade,
                "active_machines": active,
                "hardness": hardness,
                "flow_tph": flow_tph,
                "speed_std": speed_std,
                "brake_events": brake,
                "idle_ratio": idle,
                "vib_rms": vib,
                "temp_c": temp,
                "pressure_bar": press,
                "haul_rate": haul,
                "fuel_eff": fe,
                "safety_score": safety,
            }
        )

    def write_example_csv(self, path: str, n: int = 200) -> None:
        self.training_frame(n).to_csv(path, index=False)


def generate_shift_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        return {}
    speeds = [s["speed_m_s"] for s in samples]
    return {
        "count": len(samples),
        "mean_speed": float(np.mean(speeds)),
        "max_speed": float(np.max(speeds)),
        "fuel_end": samples[-1].get("fuel_l"),
    }
