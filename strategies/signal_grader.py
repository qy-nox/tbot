"""Signal grading (A+++, A++, A+, A, B, C)."""

from __future__ import annotations


def grade_signal(confidence: float) -> str:
    if confidence >= 0.95:
        return "A+++"
    if confidence >= 0.90:
        return "A++"
    if confidence >= 0.85:
        return "A+"
    if confidence >= 0.75:
        return "A"
    if confidence >= 0.60:
        return "B"
    return "C"
