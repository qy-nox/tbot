"""Utility helpers for the signal platform."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Cast any value to float safely, falling back to *default*."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_enum_value(value: Any) -> Any:
    """Extract enum .value, or return the input unchanged if not an enum."""
    return getattr(value, "value", value)


# Backward-compatible alias
enum_value = get_enum_value
