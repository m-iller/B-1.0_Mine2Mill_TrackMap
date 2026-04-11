from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.v1.stream import broadcast_sim_task, router as ws_router
from app.broker.factory import build_broker, set_broker
from app.config import get_settings
from app.services.routing_engine import RoutingEngine
from app.state import get_simulation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _bootstrap_simulation() -> None:
    sim = get_simulation()
    if sim.machines:
        return
    t1 = sim.register_machine("haul_truck", 5.0, 5.0)
    t2 = sim.register_machine("haul_truck", 8.0, 12.0)
    ex = sim.register_machine("excavator", 55.0, 60.0)
    r = RoutingEngine(sim.terrain)
    sim.terrain.hazard_mask[25][25] = True
    p1 = r.astar((t1.x, t1.y), (ex.x, ex.y))
    p2 = r.astar((t2.x, t2.y), (ex.x - 5, ex.y - 5))
    sim.set_predicted_path(t1.id, p1)
    sim.set_predicted_path(t2.id, p2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    broker = build_broker()
    set_broker(broker)
    try:
        await broker.connect()
    except Exception as e:
        logger.warning("Broker offline (OK for offline-first): %s", e)
    _bootstrap_simulation()
    task = asyncio.create_task(broadcast_sim_task())
    yield
    task.cancel()
    try:
        await broker.close()
    except Exception:
        pass
    try:
        from app.state import get_influx

        get_influx().close()
    except Exception:
        pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="MOMPS API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.include_router(ws_router)
    return app


app = create_app()


@app.get("/health")
def health():
    s = get_settings()
    return {"status": "ok", "api": s.api_version}
