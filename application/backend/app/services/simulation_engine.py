"""
Tick-based quarry simulation: machines, terrain grid, predicted paths, event hooks.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings
from app.constants import STATUS_FAILURE, STATUS_IDLE, STATUS_LOADING, STATUS_MOVING


class MachineStatus(str, Enum):
    IDLE = STATUS_IDLE
    MOVING = STATUS_MOVING
    LOADING = STATUS_LOADING
    FAILURE = STATUS_FAILURE


@dataclass
class MachineState:
    id: str
    machine_type_code: str
    x: float
    y: float
    z: float
    speed_m_s: float
    status: MachineStatus
    heading_rad: float = 0.0
    payload_t: float = 0.0
    wear_index: float = 0.0
    fuel_l: float = 500.0
    predicted_path: list[tuple[float, float, float]] = field(default_factory=list)


class TerrainModel:
    """2D elevation grid; isolines as simplified level sets."""

    def __init__(self, width: int, height: int, cell_m: float) -> None:
        self.width = width
        self.height = height
        self.cell_m = cell_m
        self.elevation: list[list[float]] = [
            [10 + 4 * math.sin(i / 6.0) * math.cos(j / 7.0) for j in range(width)] for i in range(height)
        ]
        self.hazard_mask: list[list[bool]] = [[False] * width for _ in range(height)]

    def height_at(self, x: float, y: float) -> float:
        ci, cj = int(x), int(y)
        ci = max(0, min(self.height - 1, ci))
        cj = max(0, min(self.width - 1, cj))
        return self.elevation[ci][cj]

    def isolines(self, levels: list[float]) -> list[dict[str, Any]]:
        lines: list[dict[str, Any]] = []
        for lv in levels:
            pts: list[tuple[float, float]] = []
            for i in range(self.height):
                row: list[tuple[float, float]] = []
                for j in range(self.width - 1):
                    z0, z1 = self.elevation[i][j], self.elevation[i][j + 1]
                    if (z0 - lv) * (z1 - lv) <= 0 and z0 != z1:
                        t = (lv - z0) / (z1 - z0)
                        row.append((j + t, float(i)))
                if row:
                    pts.extend(row)
            if pts:
                lines.append({"level_m": lv, "points_grid": pts})
        return lines

    def to_dict(self) -> dict[str, Any]:
        settings = get_settings()
        levels = [8.0, 10.0, 12.0, 14.0]
        return {
            "width": self.width,
            "height": self.height,
            "cell_meters": self.cell_m,
            "elevation": self.elevation,
            "isolines": self.isolines(levels),
            "feature_3d_gis": settings.feature_dem_simulation,
        }


class SimulationEngine:
    def __init__(self) -> None:
        s = get_settings()
        self.tick_seconds = s.sim_tick_seconds
        self.terrain = TerrainModel(s.sim_terrain_height, s.sim_terrain_width, s.sim_cell_meters)
        self.machines: dict[str, MachineState] = {}
        self._tick = 0
        self._listeners: list[Any] = []

    def register_machine(
        self,
        machine_type_code: str,
        x: float,
        y: float,
        mid: str | None = None,
    ) -> MachineState:
        mid = mid or str(uuid.uuid4())
        z = self.terrain.height_at(x, y)
        m = MachineState(
            id=mid,
            machine_type_code=machine_type_code,
            x=x,
            y=y,
            z=z,
            speed_m_s=0.0,
            status=MachineStatus.IDLE,
        )
        self.machines[mid] = m
        return m

    def set_predicted_path(self, machine_id: str, path: list[tuple[float, float, float]]) -> None:
        if machine_id in self.machines:
            self.machines[machine_id].predicted_path = path

    def _advance_along_path(self, m: MachineState) -> None:
        if not m.predicted_path or m.status == MachineStatus.FAILURE:
            return
        target = m.predicted_path[0]
        dx, dy = target[0] - m.x, target[1] - m.y
        dist = math.hypot(dx, dy) + 1e-6
        step = min(m.speed_m_s * self.tick_seconds / self.terrain.cell_m, dist)
        m.x += (dx / dist) * step
        m.y += (dy / dist) * step
        m.z = self.terrain.height_at(m.x, m.y)
        m.heading_rad = math.atan2(dy, dx)
        if dist < 0.35:
            m.predicted_path.pop(0)
        m.status = MachineStatus.MOVING if m.speed_m_s > 0.05 else MachineStatus.IDLE

    def tick(self) -> dict[str, Any]:
        self._tick += 1
        for m in self.machines.values():
            if m.status != MachineStatus.FAILURE:
                # simple speed profile
                if m.predicted_path:
                    m.speed_m_s = min(8.0, 3.0 + 0.5 * math.sin(self._tick / 3.0))
                self._advance_along_path(m)
                m.wear_index += 0.0001 * m.speed_m_s
                m.fuel_l -= 0.02 * m.speed_m_s * self.tick_seconds
            ci, cj = int(m.y), int(m.x)
            if 0 <= ci < self.terrain.height and 0 <= cj < self.terrain.width:
                if self.terrain.hazard_mask[ci][cj]:
                    m.status = MachineStatus.FAILURE
        snapshot = self.snapshot()
        for fn in self._listeners:
            fn(snapshot)
        return snapshot

    def snapshot(self) -> dict[str, Any]:
        predicted_future: dict[str, list[dict[str, float]]] = {}
        for mid, m in self.machines.items():
            future: list[dict[str, float]] = []
            px, py, pz = m.x, m.y, m.z
            path = list(m.predicted_path)
            t = 0.0
            spd = max(m.speed_m_s, 1.0)
            while path and t < 60.0:
                tx, ty, tz = path[0]
                dx, dy = tx - px, ty - py
                dist = math.hypot(dx, dy) + 1e-6
                step = min(spd * self.tick_seconds / self.terrain.cell_m, dist)
                px += (dx / dist) * step
                py += (dy / dist) * step
                pz = float(self.terrain.height_at(px, py))
                t += self.tick_seconds
                future.append({"t_s": t, "x": px, "y": py, "z": pz})
                if math.hypot(tx - px, ty - py) < 0.35:
                    path.pop(0)
            predicted_future[mid] = future

        return {
            "tick": self._tick,
            "tick_seconds": self.tick_seconds,
            "machines": [
                {
                    "id": m.id,
                    "type": m.machine_type_code,
                    "position": {"x": m.x, "y": m.y, "z": m.z},
                    "speed_m_s": m.speed_m_s,
                    "status": m.status.value,
                    "heading_rad": m.heading_rad,
                    "wear_index": m.wear_index,
                    "fuel_l": m.fuel_l,
                    "predicted_path": [{"x": p[0], "y": p[1], "z": p[2]} for p in m.predicted_path],
                }
                for m in self.machines.values()
            ],
            "predicted_future": predicted_future,
            "terrain": self.terrain.to_dict(),
        }
