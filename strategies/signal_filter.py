"""Signal filtering helpers."""

from __future__ import annotations


def filter_by_confidence(signals: list[dict], minimum: float = 0.7) -> list[dict]:
    return [s for s in signals if float(s.get("confidence", 0)) >= minimum]
