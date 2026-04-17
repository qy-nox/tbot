"""Formatting helpers for presenting active signals."""

from __future__ import annotations

from datetime import datetime


def _fmt_time(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def format_signal_list(signals) -> str:
    if not signals:
        return "📊 No active signals"
    lines: list[str] = ["📊 Active signals:"]
    for signal in signals:
        direction = getattr(getattr(signal, "direction", None), "value", getattr(signal, "direction", "-"))
        confidence = getattr(signal, "confidence", None)
        confidence_text = f"{confidence * 100:.0f}%" if isinstance(confidence, (float, int)) else "-"
        lines.append(
            (
                f"• #{getattr(signal, 'id', '-')}: {getattr(signal, 'pair', '-')} {direction} | "
                f"Entry: {getattr(signal, 'entry_price', '-')} | "
                f"Conf: {confidence_text} | "
                f"At: {_fmt_time(getattr(signal, 'timestamp', None))}"
            )
        )
    return "\n".join(lines)
