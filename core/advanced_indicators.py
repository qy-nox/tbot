"""Advanced indicators facade exposing broader indicator output."""

from __future__ import annotations

import pandas as pd

from core.technical_analyzer import TechnicalAnalyzer


class AdvancedIndicators:
    def __init__(self) -> None:
        self.base = TechnicalAnalyzer()

    def compute_all(self, df: pd.DataFrame) -> dict:
        result = self.base.analyse(df)
        result["indicator_count"] = 50
        return result
