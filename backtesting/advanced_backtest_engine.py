"""Advanced backtesting engine wrapper."""

from __future__ import annotations

import pandas as pd

from backtesting.backtest_engine import BacktestEngine


class AdvancedBacktestEngine(BacktestEngine):
    def walk_forward(self, df: pd.DataFrame, train_size: int = 300, step: int = 50) -> list[dict]:
        results: list[dict] = []
        for start in range(0, max(len(df) - train_size, 0), step):
            window = df.iloc[start : start + train_size]
            if len(window) < train_size:
                break
            bt = self.run(window)
            results.append({"start": start, "win_rate": bt.win_rate, "return_pct": bt.total_return_pct})
        return results
