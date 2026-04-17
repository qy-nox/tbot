"""Formatting helpers for presenting active signals."""

from __future__ import annotations

def format_signal_list(signals) -> str:
    if not signals:
        return "📊 No active signals"
    return "\n".join(f"• {s.pair}: {getattr(s.direction, 'value', s.direction)}" for s in signals)
