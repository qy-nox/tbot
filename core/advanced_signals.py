"""Consensus signal generation built on strategy and advanced indicators."""

from __future__ import annotations

import pandas as pd

from core.advanced_indicators import AdvancedIndicators
from core.sentiment_analyzer import SentimentAnalyzer
from strategies.strategy_engine import StrategyEngine


class AdvancedSignalGenerator:
    def __init__(self) -> None:
        self.indicators = AdvancedIndicators()
        self.strategy = StrategyEngine()
        self.sentiment = SentimentAnalyzer()

    def generate(self, pair: str, df: pd.DataFrame):
        analysis = self.indicators.compute_all(df)
        sentiment = self.sentiment.analyse(pair)
        return self.strategy.evaluate(pair=pair, analysis=analysis, sentiment=sentiment, atr=analysis.get("atr"))
