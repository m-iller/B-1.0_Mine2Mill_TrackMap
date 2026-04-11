from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, ml_routes, planning, reports, routing, safety, simulation, telemetry

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(telemetry.router)
api_router.include_router(simulation.router)
api_router.include_router(routing.router)
api_router.include_router(planning.router)
api_router.include_router(safety.router)
api_router.include_router(ml_routes.router)
api_router.include_router(reports.router)
