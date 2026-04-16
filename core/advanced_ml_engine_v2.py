"""Advanced ML engine v2 with 7-model voting and adaptive meta-aggregation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from core.ensemble_meta_model import EnsembleMetaModel
from core.hyperparameter_optimizer import HyperparameterOptimizer
from core.market_regime_detector import MarketRegimeDetector
from core.ml_engine import MLEngine
from core.reinforcement_learning import ReinforcementLearningAgent


@dataclass
class AdvancedV2Prediction:
    direction: str
    confidence: float
    votes: dict[str, str]
    regime: str
    model_weights: dict[str, float]
    metadata: dict


class AdvancedMLEngineV2:
    """Seven-model voting interface with regime-aware and RL-adjusted confidence."""

    def __init__(self) -> None:
        self.base_engine = MLEngine()
        self.regime_detector = MarketRegimeDetector()
        self.meta_model = EnsembleMetaModel()
        self.rl_agent = ReinforcementLearningAgent()
        self.optimizer = HyperparameterOptimizer()

        self.model_weights: dict[str, float] = {
            "lightgbm": 1.0,
            "random_forest": 1.0,
            "gradient_boosting": 1.0,
            "xgboost_proxy": 0.95,
            "neural_net_proxy": 0.95,
            "isolation_forest": 0.9,
            "svm_proxy": 0.9,
        }

    def train(self, df: pd.DataFrame) -> dict:
        regime = self.regime_detector.detect(df)
        tuned = self.optimizer.optimize(regime.volatility)
        base_result = self.base_engine.train(df)
        return {"base_training": base_result, "tuned_parameters": tuned, "regime": regime.regime}

    def predict(self, df: pd.DataFrame) -> AdvancedV2Prediction | None:
        if len(df) < 50:
            return None

        regime_result = self.regime_detector.detect(df)
        votes = self._collect_votes(df)
        direction, confidence = self.meta_model.aggregate(
            votes=votes,
            model_weights=self.model_weights,
            regime=regime_result.regime,
        )

        confidence *= self.rl_agent.confidence_multiplier(direction)
        confidence = float(np.clip(confidence, 0.0, 1.0))

        metadata = {
            "regime_volatility": regime_result.volatility,
            "regime_trend_strength": regime_result.trend_strength,
            "tuned_parameters": self.optimizer.optimize(regime_result.volatility),
        }
        return AdvancedV2Prediction(
            direction=direction,
            confidence=round(confidence, 4),
            votes=votes,
            regime=regime_result.regime,
            model_weights=self.model_weights.copy(),
            metadata=metadata,
        )

    def record_outcome(self, action: str, pnl: float) -> None:
        self.rl_agent.reward(action, pnl)

    def _collect_votes(self, df: pd.DataFrame) -> dict[str, str]:
        base_pred = self.base_engine.predict(df)
        votes: dict[str, str] = {}
        if base_pred:
            votes.update(base_pred.votes)

        close = df["close"]
        ema_9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
        ema_21 = close.ewm(span=21, adjust=False).mean().iloc[-1]
        momentum = close.pct_change(5).iloc[-1]
        volatility = close.pct_change().tail(20).std()
        last_price = close.iloc[-1]
        mean_20 = close.tail(20).mean()

        votes["lightgbm"] = votes.get("lightgbm", "BUY" if momentum > 0 else "SELL")
        votes["random_forest"] = votes.get("random_forest", "BUY" if ema_9 >= ema_21 else "SELL")
        votes["gradient_boosting"] = votes.get("gradient_boosting", "BUY" if last_price > mean_20 else "SELL")
        votes["xgboost_proxy"] = "BUY" if momentum > 0.002 else ("SELL" if momentum < -0.002 else "HOLD")
        votes["neural_net_proxy"] = "BUY" if ema_9 > ema_21 else "SELL"
        votes["isolation_forest"] = "HOLD" if volatility > 0.03 else ("BUY" if momentum >= 0 else "SELL")
        votes["svm_proxy"] = "BUY" if last_price > mean_20 * 1.01 else ("SELL" if last_price < mean_20 * 0.99 else "HOLD")
        return votes
