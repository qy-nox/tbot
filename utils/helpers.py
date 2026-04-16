"""Common helper utilities used across modules."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def chunks(items: list, size: int):
    """Yield chunks of *items* with the given *size*."""
    if size <= 0:
        raise ValueError("size must be positive")
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]
