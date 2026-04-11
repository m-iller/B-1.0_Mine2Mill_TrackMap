"""
PDF reports: shift, incident, maintenance forecast (ReportLab).
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_shift_report_pdf(data: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setTitle("MOMPS Shift Report")
    y = h - 50
    c.drawString(50, y, f"MOMPS Shift Report — {data.get('shift_code', '')}")
    y -= 24
    c.drawString(50, y, f"Generated: {datetime.now(timezone.utc).isoformat()}")
    y -= 24
    for line in data.get("lines", []):
        c.drawString(50, y, str(line)[:120])
        y -= 16
        if y < 80:
            c.showPage()
            y = h - 50
    c.showPage()
    c.save()
    return buf.getvalue()


def build_incident_report_pdf(incident: dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("MOMPS Incident Report")
    c.drawString(50, 800, "Incident Report")
    c.drawString(50, 780, f"Severity: {incident.get('severity')}")
    c.drawString(50, 760, f"Category: {incident.get('category')}")
    c.drawString(50, 740, f"Detail: {incident.get('detail')}")
    c.showPage()
    c.save()
    return buf.getvalue()


def build_maintenance_forecast_pdf(rows: list[dict[str, Any]]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle("MOMPS Maintenance Forecast")
    y = 800
    c.drawString(50, y, "Maintenance forecast (TTF estimates)")
    y -= 30
    for r in rows:
        c.drawString(50, y, f"{r.get('machine_id')} — TTF h: {r.get('ttf_h')} conf: {r.get('confidence_pct')}%")
        y -= 18
    c.showPage()
    c.save()
    return buf.getvalue()
