"""Formatting helpers for presenting active signals."""

from __future__ import annotations

from signal_platform.models import SignalRecord


def format_signal(signal: SignalRecord) -> str:
    grade = signal.grade.value if signal.grade else "-"
    confidence = f"{(signal.confidence or 0) * 100:.0f}%"
    return (
        f"{signal.pair} {signal.direction.value} | Entry: {signal.entry_price} | "
        f"TP1: {signal.take_profit_1 or '-'} | SL: {signal.stop_loss or '-'} | "
        f"Conf: {confidence} | Grade: {grade}"
    )


def format_signal_list(signals: list[SignalRecord]) -> str:
    if not signals:
        return "No active signals right now."
    return "\n".join(f"{idx + 1}. {format_signal(signal)}" for idx, signal in enumerate(signals))
