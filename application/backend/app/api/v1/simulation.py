from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.services.routing_engine import RoutingEngine
from app.state import get_simulation

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/state")
def get_state(user: str = Depends(require_user)):
    sim = get_simulation()
    return {"api_version": "v1", "user": user, **sim.snapshot()}


@router.post("/tick")
def post_tick(user: str = Depends(require_user)):
    sim = get_simulation()
    return {"api_version": "v1", "user": user, **sim.tick()}


@router.post("/route")
def compute_route(start: dict, goal: dict, user: str = Depends(require_user)):
    sim = get_simulation()
    r = RoutingEngine(sim.terrain)
    s = (float(start["x"]), float(start["y"]))
    g = (float(goal["x"]), float(goal["y"]))
    path = r.astar(s, g)
    return {"api_version": "v1", "user": user, "path": [{"x": p[0], "y": p[1], "z": p[2]} for p in path]}
