"""Signal generation and grading service."""

from __future__ import annotations

from bots.main_signal_bot.signal_engine import SignalEngine
from database.queries import create_signal


def generate_signal(db, *, pair: str, direction: str, entry_price: float, confidence: float, confirmations: int, signal_type: str = "crypto"):
    evaluation = SignalEngine.evaluate(confirmations=confirmations, confidence=confidence)
    return create_signal(
        db,
        pair=pair,
        direction=direction,
        entry_price=entry_price,
        stop_loss=None,
        tp1=None,
        tp2=None,
        tp3=None,
        grade=evaluation.grade,
        accuracy=evaluation.expected_accuracy,
        signal_type=signal_type,
        confidence=evaluation.confidence,
        strength="high" if evaluation.confidence >= 0.75 else "medium",
        validity_minutes=60,
        status="pending",
    )
