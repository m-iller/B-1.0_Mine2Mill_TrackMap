from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.services.telemetry_ingestion import ingest_telemetry
from app.state import get_influx

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/ingest")
async def ingest(body: dict, user: str = Depends(require_user)):
    influx = get_influx()
    result = await ingest_telemetry(body, influx if influx.enabled else None)
    return {"api_version": "v1", "user": user, **result}
