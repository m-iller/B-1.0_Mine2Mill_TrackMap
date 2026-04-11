"""
Store-and-forward + payload codec for mesh (site) and LoRaWAN uplink (mocked).
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MeshFrame:
    src_node_id: str
    hop_count: int
    payload: bytes
    created_unix: float = field(default_factory=time.time)


@dataclass
class LoRaWANPayloadMock:
    """Mock binary envelope: 1 byte port + JSON remainder (prototype)."""

    port: int
    data: dict[str, Any]

    def encode(self) -> bytes:
        body = json.dumps(self.data).encode("utf-8")
        return bytes([self.port & 0xFF]) + body

    @staticmethod
    def decode(raw: bytes) -> "LoRaWANPayloadMock":
        port = raw[0] if raw else 0
        data = json.loads(raw[1:].decode("utf-8")) if len(raw) > 1 else {}
        return LoRaWANPayloadMock(port=port, data=data)


class StoreForwardBuffer:
    def __init__(self, max_items: int = 10_000) -> None:
        self._max = max_items
        self._q: list[MeshFrame] = []

    def enqueue(self, frame: MeshFrame) -> bool:
        if len(self._q) >= self._max:
            return False
        self._q.append(frame)
        return True

    def dequeue_all(self) -> list[MeshFrame]:
        out = list(self._q)
        self._q.clear()
        return out


def b64_encode_frame(frame: MeshFrame) -> str:
    blob = json.dumps(
        {"src": frame.src_node_id, "hops": frame.hop_count, "t": frame.created_unix}
    ).encode() + b"|" + frame.payload
    return base64.urlsafe_b64encode(blob).decode("ascii")


def b64_decode_frame(s: str) -> MeshFrame:
    raw = base64.urlsafe_b64decode(s.encode("ascii"))
    meta_b, _, payload = raw.partition(b"|")
    meta = json.loads(meta_b.decode())
    return MeshFrame(src_node_id=meta["src"], hop_count=meta["hops"], payload=payload, created_unix=meta["t"])
