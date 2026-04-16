"""Common helper utilities used across modules."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterator


def utc_timestamp() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def chunks(items: list[Any], size: int) -> Iterator[list[Any]]:
    """Yield chunks of *items* with the given *size*."""
    if size <= 0:
        raise ValueError("size must be positive")
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]
