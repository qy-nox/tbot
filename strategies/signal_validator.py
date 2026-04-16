"""Signal validation helpers."""

from __future__ import annotations


def validate_signal(signal: dict) -> bool:
    required = {"pair", "direction", "entry_price"}
    return required.issubset(signal.keys())
