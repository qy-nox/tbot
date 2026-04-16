"""Simple auto-tuning facade for model parameters."""

from __future__ import annotations


class HyperparameterOptimizer:
    """Produces lightweight parameter sets based on volatility regime."""

    def optimize(self, volatility: float) -> dict[str, dict[str, float | int]]:
        if volatility >= 0.03:
            return {
                "lightgbm": {"n_estimators": 150, "max_depth": 4, "learning_rate": 0.03},
                "random_forest": {"n_estimators": 200, "max_depth": 7},
                "gradient_boosting": {"n_estimators": 150, "learning_rate": 0.03},
            }
        return {
            "lightgbm": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.05},
            "random_forest": {"n_estimators": 120, "max_depth": 8},
            "gradient_boosting": {"n_estimators": 100, "learning_rate": 0.05},
        }
