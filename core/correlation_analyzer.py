"""Pair correlation analysis helpers."""

from __future__ import annotations

import pandas as pd


class CorrelationAnalyzer:
    def correlation_matrix(self, closes: dict[str, pd.Series]) -> pd.DataFrame:
        frame = pd.DataFrame(closes)
        return frame.pct_change().corr()
