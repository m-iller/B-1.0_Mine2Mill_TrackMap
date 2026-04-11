from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable


class MessageBroker(ABC):
    is_connected: bool = False

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def publish(self, routing_key: str, body: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        pass
