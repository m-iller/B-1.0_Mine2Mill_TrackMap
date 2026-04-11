from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.services.planning_engine import plan_for_date

router = APIRouter(prefix="/planning", tags=["planning"])


@router.post("/shift")
def shift_plan(body: dict, user: str = Depends(require_user)):
    d = date.fromisoformat(body.get("date", date.today().isoformat()))
    code = body.get("shift_code", "A")
    machines = body.get("machine_ids", ["m1", "m2", "m3"])
    plan = plan_for_date(d, code, machines)
    return {"api_version": "v1", "user": user, **plan}
