"""
Lightweight AI/ML prediction engine.

Uses a three-model voting ensemble (LightGBM, Random Forest, Gradient Boosting)
for signal confirmation.  All models are CPU-only and train on standard OHLCV +
indicator features.
"""

import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import BASE_DIR

logger = logging.getLogger("trading_bot.ml_engine")

MODEL_CACHE_DIR = BASE_DIR / "model_cache"


@dataclass
class MLPrediction:
    """Result of the ensemble prediction."""

    direction: str          # BUY / SELL / HOLD
    confidence: float       # 0-1 probability of the predicted direction
    votes: dict[str, str]   # model_name -> vote
    probabilities: dict[str, float]  # model_name -> confidence


class MLEngine:
    """Three-model voting ensemble for signal confirmation."""

    def __init__(self) -> None:
        self.models: dict = {}
        self._is_trained = False
        MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._try_load_cached()

    # ── Feature engineering ─────────────────────────────────────────────

    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create ML features from OHLCV data.

        Returns a DataFrame with one row per candle and ~20 feature columns.
        """
        feat = pd.DataFrame(index=df.index)

        # Price-based
        feat["returns_1"] = df["close"].pct_change(1)
        feat["returns_3"] = df["close"].pct_change(3)
        feat["returns_5"] = df["close"].pct_change(5)
        feat["returns_10"] = df["close"].pct_change(10)

        # Volatility
        feat["volatility_5"] = df["close"].rolling(5).std() / df["close"]
        feat["volatility_10"] = df["close"].rolling(10).std() / df["close"]
        feat["volatility_20"] = df["close"].rolling(20).std() / df["close"]

        # Volume features
        feat["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
        feat["volume_change"] = df["volume"].pct_change(1)

        # Price position
        high_20 = df["high"].rolling(20).max()
        low_20 = df["low"].rolling(20).min()
        range_20 = high_20 - low_20
        feat["price_position"] = (df["close"] - low_20) / range_20.replace(0, np.nan)

        # Candle features
        body = (df["close"] - df["open"]).abs()
        candle_range = df["high"] - df["low"]
        feat["body_ratio"] = body / candle_range.replace(0, np.nan)
        feat["upper_shadow"] = (df["high"] - df[["close", "open"]].max(axis=1)) / candle_range.replace(0, np.nan)
        feat["lower_shadow"] = (df[["close", "open"]].min(axis=1) - df["low"]) / candle_range.replace(0, np.nan)

        # RSI
        delta = df["close"].diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, min_periods=14).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, min_periods=14).mean()
        rs = gain / loss.replace(0, np.nan)
        feat["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        feat["macd"] = ema12 - ema26
        feat["macd_signal"] = feat["macd"].ewm(span=9, adjust=False).mean()
        feat["macd_hist"] = feat["macd"] - feat["macd_signal"]

        # EMA distances
        ema20 = df["close"].ewm(span=20, adjust=False).mean()
        ema50 = df["close"].ewm(span=50, adjust=False).mean()
        feat["ema20_dist"] = (df["close"] - ema20) / ema20
        feat["ema50_dist"] = (df["close"] - ema50) / ema50

        # ATR
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - df["close"].shift()).abs(),
            (df["low"] - df["close"].shift()).abs(),
        ], axis=1).max(axis=1)
        feat["atr_ratio"] = tr.rolling(14).mean() / df["close"]

        feat.dropna(inplace=True)
        return feat

    @staticmethod
    def build_labels(df: pd.DataFrame, horizon: int = 5, threshold: float = 0.005) -> pd.Series:
        """Create classification labels based on future returns.

        Labels: 1 = BUY (price rises > threshold), -1 = SELL, 0 = HOLD.
        """
        future_return = df["close"].shift(-horizon) / df["close"] - 1
        labels = pd.Series(0, index=df.index, dtype=int)
        labels[future_return > threshold] = 1
        labels[future_return < -threshold] = -1
        return labels

    # ── Training ────────────────────────────────────────────────────────

    def train(self, df: pd.DataFrame, horizon: int = 5) -> dict:
        """Train the three-model ensemble on the given OHLCV data.

        Returns a dict with per-model accuracy on a holdout set.
        """
        try:
            from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
            import lightgbm as lgb
        except ImportError as exc:
            logger.error("ML dependencies not installed: %s", exc)
            return {}

        features = self.build_features(df)
        labels = self.build_labels(df, horizon=horizon)

        # Align
        common_idx = features.index.intersection(labels.index)
        features = features.loc[common_idx]
        labels = labels.loc[common_idx]

        # Remove trailing rows where future data is unavailable
        if horizon > 0:
            features = features.iloc[:-horizon]
            labels = labels.iloc[:-horizon]

        if len(features) < 100:
            logger.warning("Not enough data for ML training (%d rows)", len(features))
            return {}

        # Train / test split (time-based, no shuffle)
        split = int(len(features) * 0.8)
        X_train, X_test = features.iloc[:split], features.iloc[split:]
        y_train, y_test = labels.iloc[:split], labels.iloc[split:]

        results = {}

        # Model 1: LightGBM
        try:
            lgb_model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=20,
                verbose=-1,
            )
            lgb_model.fit(X_train, y_train)
            acc = lgb_model.score(X_test, y_test)
            self.models["lightgbm"] = lgb_model
            results["lightgbm"] = acc
            logger.info("LightGBM trained – accuracy %.2f%%", acc * 100)
        except Exception:
            logger.exception("LightGBM training failed")

        # Model 2: Random Forest
        try:
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                min_samples_leaf=10,
                n_jobs=-1,
                random_state=42,
            )
            rf_model.fit(X_train, y_train)
            acc = rf_model.score(X_test, y_test)
            self.models["random_forest"] = rf_model
            results["random_forest"] = acc
            logger.info("RandomForest trained – accuracy %.2f%%", acc * 100)
        except Exception:
            logger.exception("RandomForest training failed")

        # Model 3: Gradient Boosting
        try:
            gb_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                min_samples_leaf=10,
                random_state=42,
            )
            gb_model.fit(X_train, y_train)
            acc = gb_model.score(X_test, y_test)
            self.models["gradient_boosting"] = gb_model
            results["gradient_boosting"] = acc
            logger.info("GradientBoosting trained – accuracy %.2f%%", acc * 100)
        except Exception:
            logger.exception("GradientBoosting training failed")

        if self.models:
            self._is_trained = True
            self._save_cache()

        return results

    # ── Prediction ──────────────────────────────────────────────────────

    def predict(self, df: pd.DataFrame) -> Optional[MLPrediction]:
        """Run the ensemble and return a voted prediction."""
        if not self._is_trained or not self.models:
            logger.debug("ML engine not trained – skipping prediction")
            return None

        features = self.build_features(df)
        if features.empty:
            return None

        last_row = features.iloc[[-1]]
        votes: dict[str, str] = {}
        probabilities: dict[str, float] = {}
        label_map = {1: "BUY", -1: "SELL", 0: "HOLD"}

        for name, model in self.models.items():
            try:
                pred = model.predict(last_row)[0]
                proba = model.predict_proba(last_row)[0]
                pred_label = label_map.get(pred, "HOLD")
                confidence = float(max(proba))
                votes[name] = pred_label
                probabilities[name] = confidence
            except Exception:
                logger.exception("Prediction failed for %s", name)

        if not votes:
            return None

        # Majority vote
        vote_counts: dict[str, int] = {}
        for v in votes.values():
            vote_counts[v] = vote_counts.get(v, 0) + 1

        direction = max(vote_counts, key=lambda k: vote_counts[k])
        agreeing = vote_counts[direction]
        total = len(votes)
        agreeing_probs = [p for n, p in probabilities.items() if votes[n] == direction]
        avg_conf = float(np.mean(agreeing_probs)) if agreeing_probs else 0.0

        prediction = MLPrediction(
            direction=direction,
            confidence=round(float(avg_conf * agreeing / total), 4),
            votes=votes,
            probabilities=probabilities,
        )
        logger.info(
            "ML prediction: %s (conf=%.1f%%) votes=%s",
            prediction.direction,
            prediction.confidence * 100,
            prediction.votes,
        )
        return prediction

    # ── Model caching ───────────────────────────────────────────────────

    def _save_cache(self) -> None:
        """Persist trained models to disk."""
        for name, model in self.models.items():
            path = MODEL_CACHE_DIR / f"{name}.pkl"
            try:
                with open(path, "wb") as fh:
                    pickle.dump(model, fh)
                logger.debug("Cached model %s → %s", name, path)
            except Exception:
                logger.exception("Failed to cache model %s", name)

    def _try_load_cached(self) -> None:
        """Load previously trained models from cache."""
        model_names = ["lightgbm", "random_forest", "gradient_boosting"]
        loaded = 0
        for name in model_names:
            path = MODEL_CACHE_DIR / f"{name}.pkl"
            if path.exists():
                try:
                    with open(path, "rb") as fh:
                        self.models[name] = pickle.load(fh)
                    loaded += 1
                except Exception:
                    logger.exception("Failed to load cached model %s", name)
        if loaded > 0:
            self._is_trained = True
            logger.info("Loaded %d cached ML models", loaded)

    @property
    def is_ready(self) -> bool:
        """Return True if models have been trained or loaded from cache."""
        return self._is_trained
