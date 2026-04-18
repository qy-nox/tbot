"""Signal grading engine aligned with B/A/A+ accuracy tiers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalEvaluation:
    """Signal quality output used by distribution and reporting."""

    grade: str
    confidence: float
    expected_accuracy: int


class SignalEngine:
    """Evaluate signals using requirement-aligned thresholds."""

    @staticmethod
    def evaluate(*, confirmations: int, confidence: float) -> SignalEvaluation:
        """Return grade and expected accuracy from confidence/confirmation depth."""
        normalized = max(0.0, min(confidence, 1.0))
        if confirmations >= 5 and normalized >= 0.90:
            return SignalEvaluation(grade="A+", confidence=normalized, expected_accuracy=99)
        if confirmations >= 3 and normalized >= 0.75:
            return SignalEvaluation(grade="A", confidence=normalized, expected_accuracy=85)
        if confirmations >= 1 and normalized >= 0.60:
            return SignalEvaluation(grade="B", confidence=normalized, expected_accuracy=70)
        return SignalEvaluation(grade="B", confidence=normalized, expected_accuracy=70)
