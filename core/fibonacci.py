"""
Fibonacci retracement and extension module.

Provides standalone Fibonacci level computation that can be used by
TechnicalAnalyzer, SMCAnalyzer, or any other component that needs
price-based Fibonacci levels.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger("trading_bot.fibonacci")

# Standard Fibonacci ratios
RETRACEMENT_RATIOS = {
    "fib_0.0": 0.0,
    "fib_23.6": 0.236,
    "fib_38.2": 0.382,
    "fib_50.0": 0.500,
    "fib_61.8": 0.618,
    "fib_78.6": 0.786,
    "fib_100.0": 1.0,
}

EXTENSION_RATIOS = {
    "fib_ext_127.2": 1.272,
    "fib_ext_161.8": 1.618,
    "fib_ext_200.0": 2.000,
    "fib_ext_261.8": 2.618,
}


def compute_retracements(
    high: float, low: float
) -> dict[str, float]:
    """Compute Fibonacci retracement levels from a swing high and swing low.

    Parameters
    ----------
    high:
        The swing high price.
    low:
        The swing low price.

    Returns
    -------
    dict mapping level name → price
    """
    diff = high - low
    if diff <= 0:
        logger.warning("fibonacci.compute_retracements: high <= low (diff=%s)", diff)
        return {}

    levels: dict[str, float] = {}
    for name, ratio in RETRACEMENT_RATIOS.items():
        levels[name] = round(high - ratio * diff, 8)
    return levels


def compute_extensions(
    high: float, low: float, swing_start: float | None = None
) -> dict[str, float]:
    """Compute Fibonacci extension levels.

    If *swing_start* is provided it is used as the base for projection
    (e.g. the prior swing low for a bullish move).  Otherwise *low* is used.

    Parameters
    ----------
    high:
        The swing high price.
    low:
        The swing low price (end of retracement).
    swing_start:
        Optional prior swing point to project from.

    Returns
    -------
    dict mapping level name → price
    """
    base = swing_start if swing_start is not None else low
    diff = high - low
    if diff <= 0:
        logger.warning("fibonacci.compute_extensions: high <= low (diff=%s)", diff)
        return {}

    levels: dict[str, float] = {}
    for name, ratio in EXTENSION_RATIOS.items():
        levels[name] = round(base + ratio * diff, 8)
    return levels


def auto_levels(
    df: pd.DataFrame,
    lookback: int = 50,
    include_extensions: bool = False,
) -> dict[str, float]:
    """Automatically detect the swing high/low over *lookback* bars
    and return Fibonacci retracement (and optionally extension) levels.

    Parameters
    ----------
    df:
        OHLCV DataFrame with at minimum ``high`` and ``low`` columns.
    lookback:
        Number of recent bars to consider for the swing range.
    include_extensions:
        When True, extension levels are included in the result.

    Returns
    -------
    dict mapping Fibonacci level label → price
    """
    if df.empty or len(df) < 2:
        logger.warning("fibonacci.auto_levels: insufficient data")
        return {}

    df_cols = [str(c).lower() for c in df.columns]
    if "high" not in df_cols or "low" not in df_cols:
        logger.warning("fibonacci.auto_levels: missing high/low columns")
        return {}

    df_copy = df.copy()
    df_copy.columns = df_cols

    recent = df_copy.tail(lookback)
    swing_high = float(recent["high"].max())
    swing_low = float(recent["low"].min())

    levels = compute_retracements(swing_high, swing_low)

    if include_extensions:
        ext = compute_extensions(swing_high, swing_low)
        levels.update(ext)

    logger.debug(
        "Fibonacci auto_levels: high=%.6f low=%.6f levels=%s",
        swing_high,
        swing_low,
        list(levels.keys()),
    )
    return levels


def nearest_level(
    price: float,
    levels: dict[str, float],
) -> tuple[str, float] | None:
    """Return the (name, price) of the Fibonacci level nearest to *price*.

    Returns ``None`` when *levels* is empty.
    """
    if not levels:
        return None
    best = min(levels.items(), key=lambda kv: abs(kv[1] - price))
    return best


def is_near_level(
    price: float,
    levels: dict[str, float],
    tolerance_pct: float = 0.005,
) -> bool:
    """Return True when *price* is within *tolerance_pct* of any Fibonacci level.

    Note: assumes Fibonacci levels represent prices, which must be non-zero
    (including negative prices for CFD instruments).  Levels at zero are skipped.
    """
    for level_price in levels.values():
        if abs(level_price) > 1e-10:
            if abs(price - level_price) / abs(level_price) <= tolerance_pct:
                return True
    return False
