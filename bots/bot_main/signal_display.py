"""Formatting helpers for presenting active signals."""

from __future__ import annotations

from signal_platform.models import SignalOutcome, SignalRecord, get_session

MAX_DISPLAYED_SIGNALS = 10


def format_signal_list(signals) -> str:
    """Format a list of signal records into Telegram HTML text."""
    if not signals:
        return "📊 No active signals"

    lines = ["📈 <b>Active Trading Signals:</b>\n"]
    direction_to_emoji = {"BUY": "📈", "SELL": "📉"}
    for signal in signals[:MAX_DISPLAYED_SIGNALS]:
        emoji = direction_to_emoji.get(signal.direction.value, "📊")
        lines.append(
            f"{emoji} <b>{signal.pair}</b> {signal.direction.value}\n"
            f"  Entry: {signal.entry_price}\n"
            f"  Confidence: {signal.confidence:.0%}\n"
        )
    return "\n".join(lines)
