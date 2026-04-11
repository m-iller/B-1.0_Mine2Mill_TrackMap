from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.state import get_simulation

router = APIRouter()


class Hub:
    def __init__(self) -> None:
        self.clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.clients:
            self.clients.remove(ws)

    async def broadcast(self, msg: dict) -> None:
        dead: list[WebSocket] = []
        for c in self.clients:
            try:
                await c.send_text(json.dumps(msg))
            except Exception:
                dead.append(c)
        for d in dead:
            self.disconnect(d)


hub = Hub()


@router.websocket("/ws/v1/stream")
async def stream(ws: WebSocket):
    await hub.connect(ws)
    try:
        while True:
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        hub.disconnect(ws)


async def broadcast_sim_task() -> None:
    while True:
        await asyncio.sleep(2)
        sim = get_simulation()
        snap = sim.tick()
        await hub.broadcast({"type": "simulation", "payload": snap})
