"""Market profile and volume analysis helpers."""

from __future__ import annotations

import pandas as pd


class MarketProfile:
    def volume_profile(self, df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
        data = df[["close", "volume"]].copy()
        data["price_bin"] = pd.cut(data["close"], bins=bins)
        profile = data.groupby("price_bin", observed=False)["volume"].sum().reset_index()
        return profile
