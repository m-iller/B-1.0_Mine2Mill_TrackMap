from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.services.routing_engine import RoutingEngine
from app.state import get_simulation

router = APIRouter(prefix="/routing", tags=["routing"])


@router.post("/reroute")
def reroute(context: dict, user: str = Depends(require_user)):
    sim = get_simulation()
    r = RoutingEngine(sim.terrain)
    reasons = r.reroute_triggers(context)
    return {"api_version": "v1", "user": user, "reasons": reasons}


@router.post("/jit")
def jit(body: dict, user: str = Depends(require_user)):
    sim = get_simulation()
    r = RoutingEngine(sim.terrain)
    adv = r.jit_speed_advice(float(body.get("truck_eta_s", 0)), float(body.get("excavator_ready_s", 0)))
    return {"api_version": "v1", "user": user, **adv}
