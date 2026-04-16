"""Supply and demand zone analysis helpers."""

from __future__ import annotations

import pandas as pd

from core.technical_analyzer import TechnicalAnalyzer


class SupplyDemandAnalyzer:
    def __init__(self) -> None:
        self.ta = TechnicalAnalyzer()

    def zones(self, df: pd.DataFrame) -> dict:
        sr = self.ta.compute_support_resistance(df)
        sd = self.ta.compute_supply_demand_zones(df)
        return {
            "supports": sr["supports"],
            "resistances": sr["resistances"],
            "demand": sd["demand"],
            "supply": sd["supply"],
        }
