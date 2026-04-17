"""Formatting helpers for presenting active signals."""

from __future__ import annotations

def format_signal_list(signals) -> str:
    if not signals:
        return "📊 No active signals"
    return "\n".join(
        f"• {getattr(s, 'pair', '-')}: {getattr(getattr(s, 'direction', None), 'value', getattr(s, 'direction', '-'))}"
        for s in signals
    )
