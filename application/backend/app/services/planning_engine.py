"""
Shift/daily planning: allocate machines, forecast completion (target ±5% band).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import random


@dataclass
class PlanInputs:
    target_tonnes: float
    available_machine_ids: list[str]
    maintenance_blocks: list[tuple[datetime, datetime]]
    shift_start: datetime
    shift_end: datetime


@dataclass
class PlanOutputs:
    tasks: list[dict[str, Any]]
    forecast_tonnes: float
    forecast_error_pct: float


class ProductionPlanningEngine:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng or random.Random(42)

    def build_shift_plan(self, inp: PlanInputs) -> PlanOutputs:
        hours = max((inp.shift_end - inp.shift_start).total_seconds() / 3600.0, 0.01)
        base_rate = 180.0 / hours  # tonnes per hour aggregate stub
        noise = self._rng.uniform(-0.04, 0.04)
        forecast = inp.target_tonnes * (1.0 + noise)
        forecast = max(forecast, inp.target_tonnes * 0.9)
        err_pct = abs(forecast - inp.target_tonnes) / inp.target_tonnes * 100 if inp.target_tonnes else 0.0

        tasks: list[dict[str, Any]] = []
        slot = inp.shift_start
        chunk = inp.target_tonnes / max(len(inp.available_machine_ids), 1)
        for mid in inp.available_machine_ids:
            tasks.append(
                {
                    "id": str(uuid4()),
                    "machine_id": mid,
                    "task_type": "haul_cycle",
                    "target_tonnes": round(chunk, 2),
                    "scheduled_start": slot.isoformat(),
                    "scheduled_end": (slot + timedelta(hours=1)).isoformat(),
                }
            )
            slot += timedelta(minutes=45)

        return PlanOutputs(tasks=tasks, forecast_tonnes=forecast, forecast_error_pct=round(err_pct, 2))

    def replan_realtime(
        self,
        current_progress_t: float,
        target_t: float,
        remaining_hours: float,
    ) -> dict[str, Any]:
        gap = target_t - current_progress_t
        required_rate = gap / max(remaining_hours, 1e-3)
        return {
            "gap_tonnes": gap,
            "required_rate_tph": round(required_rate, 2),
            "actions": ["add_truck" if required_rate > 220 else "hold", "defer_non_critical_loads"],
        }


def plan_for_date(shift_date: date, shift_code: str, machines: list[str]) -> dict[str, Any]:
    start = datetime(shift_date.year, shift_date.month, shift_date.day, 6, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=8)
    eng = ProductionPlanningEngine()
    out = eng.build_shift_plan(
        PlanInputs(
            target_tonnes=12_000.0,
            available_machine_ids=machines,
            maintenance_blocks=[],
            shift_start=start,
            shift_end=end,
        )
    )
    return {
        "shift_code": shift_code,
        "tasks": out.tasks,
        "forecast_tonnes": out.forecast_tonnes,
        "forecast_error_pct": out.forecast_error_pct,
        "within_target_band": out.forecast_error_pct <= 5.0,
    }
