"""Meta-model that votes on model votes."""

from __future__ import annotations


class EnsembleMetaModel:
    """Weighted aggregation layer over model-level predictions."""

    regime_multipliers = {
        "TRENDING": {"BUY": 1.15, "SELL": 1.15, "HOLD": 0.8},
        "RANGING": {"BUY": 0.95, "SELL": 0.95, "HOLD": 1.2},
        "VOLATILE": {"BUY": 0.9, "SELL": 0.9, "HOLD": 1.1},
    }

    def aggregate(
        self,
        votes: dict[str, str],
        model_weights: dict[str, float] | None = None,
        regime: str = "RANGING",
    ) -> tuple[str, float]:
        if not votes:
            return "HOLD", 0.0

        weights = model_weights or {}
        direction_scores: dict[str, float] = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        multipliers = self.regime_multipliers.get(regime, self.regime_multipliers["RANGING"])

        total_weight = 0.0
        for model_name, direction in votes.items():
            weight = float(weights.get(model_name, 1.0))
            adjusted = weight * multipliers.get(direction, 1.0)
            direction_scores[direction] = direction_scores.get(direction, 0.0) + adjusted
            total_weight += adjusted

        if total_weight <= 0:
            return "HOLD", 0.0

        direction = max(direction_scores, key=lambda candidate: direction_scores[candidate])
        confidence = direction_scores[direction] / total_weight
        return direction, round(float(confidence), 4)
