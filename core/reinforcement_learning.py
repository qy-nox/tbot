"""Lightweight reinforcement feedback loop for signal calibration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReinforcementLearningAgent:
    """Tracks action outcomes and returns confidence multipliers."""

    learning_rate: float = 0.05
    action_scores: dict[str, float] = field(
        default_factory=lambda: {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
    )

    def reward(self, action: str, pnl: float) -> None:
        key = action.upper()
        if key not in self.action_scores:
            self.action_scores[key] = 0.0
        self.action_scores[key] += self.learning_rate * pnl

    def confidence_multiplier(self, action: str) -> float:
        score = self.action_scores.get(action.upper(), 0.0)
        return max(0.7, min(1.3, 1.0 + score))
