"""
Future extension hooks — no blocking broker calls from sync context.
Services should await broker.publish from async paths when needed.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def emit_extension_event(hook_type: str, payload: dict[str, Any]) -> None:
    """Log + buffer for async flush; wire to broker in ingestion pipeline."""
    logger.debug("extension_hook %s %s", hook_type, payload)
