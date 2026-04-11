from __future__ import annotations

import json
import logging
from typing import Any, Awaitable, Callable

import aio_pika

from app.broker.base import MessageBroker

logger = logging.getLogger(__name__)


class RabbitMQBroker(MessageBroker):
    def __init__(self, url: str) -> None:
        self._url = url
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self.is_connected = False

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        self.is_connected = True
        logger.info("RabbitMQ connected")

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
        self.is_connected = False

    async def publish(self, routing_key: str, body: dict[str, Any]) -> None:
        if not self._channel:
            return
        exchange = await self._channel.declare_exchange("momps.topic", aio_pika.ExchangeType.TOPIC, durable=True)
        msg = aio_pika.Message(body=json.dumps(body).encode("utf-8"), content_type="application/json")
        await exchange.publish(msg, routing_key=routing_key)

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if not self._channel:
            return
        exchange = await self._channel.declare_exchange("momps.topic", aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await self._channel.declare_queue(queue_name, durable=True)
        for key in routing_keys:
            await queue.bind(exchange, routing_key=key)

        async def on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                data = json.loads(message.body.decode("utf-8"))
                await handler(data)

        await queue.consume(on_message)
