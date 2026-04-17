"""Multi-confirmation logic for trading signal quality scoring."""

from __future__ import annotations


class MultiConfirmationSystem:
    BASE_REQUIREMENTS = ("rsi", "macd", "ema_alignment")

    def evaluate(self, checks: dict[str, bool]) -> dict[str, int | float | bool]:
        count = sum(1 for ok in checks.values() if ok)
        base_ok = all(checks.get(name, False) for name in self.BASE_REQUIREMENTS)

        if count >= 8:
            confidence = 95
        elif count >= 6:
            confidence = 85
        elif count >= 4:
            confidence = 75
        elif count >= 3:
            confidence = 60
        else:
            confidence = 0

        return {
            "confirmations": count,
            "base_requirements_met": base_ok,
            "confidence": confidence,
            "is_valid": base_ok and count >= 3,
        }
