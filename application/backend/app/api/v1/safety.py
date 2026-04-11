from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.services.safety_system import OperatorSafetySystem
from app.state import get_simulation

router = APIRouter(prefix="/safety", tags=["safety"])


@router.post("/evaluate")
def evaluate(sample: dict, user: str = Depends(require_user)):
    sys = OperatorSafetySystem()
    alerts = [asdict(a) for a in sys.evaluate_telemetry(sample)]
    return {"api_version": "v1", "user": user, "alerts": alerts}


@router.post("/proximity")
def proximity(user: str = Depends(require_user)):
    sim = get_simulation()
    snap = sim.snapshot()
    machines = snap.get("machines", [])
    cell_m = float(snap.get("terrain", {}).get("cell_meters", 10.0))
    sys = OperatorSafetySystem()
    alerts = [asdict(a) for a in sys.proximity_scan(machines, cell_meters=cell_m)]
    return {"api_version": "v1", "user": user, "alerts": alerts}
