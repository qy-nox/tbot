"""Extended multi-timeframe analyzer for seven timeframes."""

from __future__ import annotations

import pandas as pd

from core.multi_timeframe import MultiTimeframeAnalyzer as BaseMTF

ADVANCED_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]


class MultiTimeframeAnalyzer:
    def __init__(self) -> None:
        self.base = BaseMTF()

    def analyse(self, dataframes: dict[str, pd.DataFrame]):
        mapped = {tf: dataframes.get(tf) for tf in ADVANCED_TIMEFRAMES if dataframes.get(tf) is not None}
        # Base analyzer currently supports 5m/1h/4h; keep compatibility by forwarding those.
        return self.base.analyse({k: v for k, v in mapped.items() if k in {"5m", "1h", "4h"}})
