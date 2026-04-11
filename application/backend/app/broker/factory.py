from __future__ import annotations

from app.broker.base import MessageBroker
from app.broker.kafka_backend import KafkaBrokerStub
from app.broker.rabbitmq_backend import RabbitMQBroker
from app.config import get_settings

_broker: MessageBroker | None = None


def get_broker() -> MessageBroker | None:
    return _broker


def build_broker() -> MessageBroker:
    settings = get_settings()
    if settings.broker_backend == "kafka":
        return KafkaBrokerStub("localhost:9092")
    return RabbitMQBroker(settings.rabbit_url)


def set_broker(b: MessageBroker | None) -> None:
    global _broker
    _broker = b
