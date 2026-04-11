from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.deps import require_user
from app.services.reporting_service import (
    build_incident_report_pdf,
    build_maintenance_forecast_pdf,
    build_shift_report_pdf,
)
from app.state import get_ml

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/shift.pdf")
def shift_pdf(user: str = Depends(require_user)):
    data = {"shift_code": "A", "lines": ["Production OK", "Fuel within band", "Zero LTI"]}
    pdf = build_shift_report_pdf(data)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=shift.pdf"})


@router.get("/incident.pdf")
def incident_pdf(user: str = Depends(require_user)):
    pdf = build_incident_report_pdf({"severity": "warning", "category": "proximity", "detail": {"dist_m": 18}})
    return Response(content=pdf, media_type="application/pdf")


@router.get("/maintenance.pdf")
def maintenance_pdf(user: str = Depends(require_user)):
    pipe = get_ml()
    pr = pipe.predict_ttf(400, 12)
    rows = [{"machine_id": "m-1", "ttf_h": round(pr.value, 1), "confidence_pct": pr.confidence_pct}]
    pdf = build_maintenance_forecast_pdf(rows)
    return Response(content=pdf, media_type="application/pdf")
