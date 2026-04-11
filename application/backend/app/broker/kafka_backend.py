"""
Kafka backend stub — same interface as RabbitMQ; implement aiokafka producer/consumer later.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from app.broker.base import MessageBroker

logger = logging.getLogger(__name__)


class KafkaBrokerStub(MessageBroker):
    def __init__(self, _bootstrap_servers: str) -> None:
        self.is_connected = False

    async def connect(self) -> None:
        logger.warning("Kafka backend not implemented; running no-op broker")
        self.is_connected = False

    async def close(self) -> None:
        self.is_connected = False

    async def publish(self, routing_key: str, body: dict[str, Any]) -> None:
        logger.debug("Kafka stub publish skipped: %s", routing_key)

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        logger.debug("Kafka stub subscribe skipped: %s", queue_name)
