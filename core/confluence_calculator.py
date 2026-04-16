"""Confluence score calculation utilities."""

from __future__ import annotations


def calculate_confluence(scores: dict[str, float]) -> float:
    if not scores:
        return 0.0
    bounded = [max(0.0, min(1.0, v)) for v in scores.values()]
    return sum(bounded) / len(bounded)
