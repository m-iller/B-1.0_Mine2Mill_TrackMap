"""
Graph routing with multi-objective cost: distance, fuel, wear, safety risk.
A* on grid graph; dynamic re-route on failure / bottleneck / safety.
"""

from __future__ import annotations

import heapq
import math
from typing import Any

from app.services.simulation_engine import TerrainModel


class RoutingEngine:
    def __init__(self, terrain: TerrainModel) -> None:
        self.terrain = terrain
        self.w_distance = 1.0
        self.w_fuel = 0.15
        self.w_wear = 0.08
        self.w_risk = 2.5

    def neighbors(self, i: int, j: int) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1)):
            ni, nj = i + di, j + dj
            if 0 <= ni < self.terrain.height and 0 <= nj < self.terrain.width:
                out.append((ni, nj))
        return out

    def edge_cost(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        i1, j1 = a
        i2, j2 = b
        z1 = self.terrain.elevation[i1][j1]
        z2 = self.terrain.elevation[i2][j2]
        dist = math.hypot(i2 - i1, j2 - j1) * self.terrain.cell_m
        grade = abs(z2 - z1) / max(dist, 1e-3)
        fuel = dist * (1.0 + 2.0 * grade)
        wear = dist * (1.0 + grade) * 0.02
        risk = 3.0 if self.terrain.hazard_mask[i2][j2] else 0.0
        risk += grade * 0.5
        return self.w_distance * dist + self.w_fuel * fuel + self.w_wear * wear + self.w_risk * risk

    def astar(
        self,
        start: tuple[float, float],
        goal: tuple[float, float],
    ) -> list[tuple[float, float, float]]:
        si, sj = int(start[1]), int(start[0])
        gi, gj = int(goal[1]), int(goal[0])
        si = max(0, min(self.terrain.height - 1, si))
        sj = max(0, min(self.terrain.width - 1, sj))
        gi = max(0, min(self.terrain.height - 1, gi))
        gj = max(0, min(self.terrain.width - 1, gj))
        start_n = (si, sj)
        goal_n = (gi, gj)

        def h(n: tuple[int, int]) -> float:
            return math.hypot(n[0] - goal_n[0], n[1] - goal_n[1]) * self.terrain.cell_m

        open_heap: list[tuple[float, int, int]] = []
        heapq.heappush(open_heap, (h(start_n), start_n[0], start_n[1]))
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start_n: None}
        gscore: dict[tuple[int, int], float] = {start_n: 0.0}

        while open_heap:
            _, ci, cj = heapq.heappop(open_heap)
            current = (ci, cj)
            if current == goal_n:
                path: list[tuple[int, int]] = []
                c: tuple[int, int] | None = current
                while c is not None:
                    path.append(c)
                    c = came_from[c]
                path.reverse()
                return [
                    (
                        float(j),
                        float(i),
                        float(self.terrain.elevation[i][j]),
                    )
                    for i, j in path
                ]
            for nb in self.neighbors(*current):
                tentative = gscore[current] + self.edge_cost(current, nb)
                if tentative < gscore.get(nb, float("inf")):
                    came_from[nb] = current
                    gscore[nb] = tentative
                    f = tentative + h(nb)
                    heapq.heappush(open_heap, (f, nb[0], nb[1]))
        return []

    def reroute_triggers(self, context: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if context.get("equipment_failure"):
            reasons.append("equipment_failure")
        if context.get("bottleneck_score", 0) > 0.75:
            reasons.append("bottleneck")
        if context.get("safety_violation"):
            reasons.append("safety_violation")
        return reasons

    def jit_speed_advice(self, truck_eta_s: float, excavator_ready_s: float) -> dict[str, float]:
        delta = excavator_ready_s - truck_eta_s
        if delta > 30:
            return {"advice": "slow", "target_speed_factor": max(0.4, 1.0 - min(delta, 120) / 300)}
        if delta < -30:
            return {"advice": "hurry", "target_speed_factor": min(1.3, 1.0 + min(-delta, 120) / 200)}
        return {"advice": "hold", "target_speed_factor": 1.0}
