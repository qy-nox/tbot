"""Synchronize timeframe signals."""

from __future__ import annotations


def sync_signals(timeframe_directions: dict[str, str]) -> str:
    if not timeframe_directions:
        return "NEUTRAL"
    buy = sum(1 for d in timeframe_directions.values() if d == "BUY")
    sell = sum(1 for d in timeframe_directions.values() if d == "SELL")
    if buy > sell:
        return "BUY"
    if sell > buy:
        return "SELL"
    return "NEUTRAL"
