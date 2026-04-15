"""
Technical analysis module.
Computes RSI, EMA, MACD, Bollinger Bands, ATR, ADX,
Fibonacci retracement levels, and support/resistance zones.
"""

import logging

import numpy as np
import pandas as pd

from config.settings import Settings

logger = logging.getLogger("trading_bot.technical_analyzer")


class TechnicalAnalyzer:
    """Calculate technical indicators on OHLCV DataFrames."""

    def __init__(self) -> None:
        self.cfg = Settings.INDICATORS

    # ── RSI ─────────────────────────────────────────────────────────────

    def compute_rsi(self, df: pd.DataFrame, period: int | None = None) -> pd.Series:
        """Relative Strength Index."""
        period = period or self.cfg["rsi"]["period"]
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        logger.debug("RSI(%d) computed", period)
        return rsi

    # ── EMA ─────────────────────────────────────────────────────────────

    def compute_ema(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Exponential Moving Average."""
        ema = df["close"].ewm(span=period, adjust=False).mean()
        logger.debug("EMA(%d) computed", period)
        return ema

    def compute_ema_set(self, df: pd.DataFrame) -> dict[str, pd.Series]:
        """Return fast / medium / slow EMAs."""
        cfg = self.cfg["ema"]
        return {
            "ema_fast": self.compute_ema(df, cfg["fast"]),
            "ema_medium": self.compute_ema(df, cfg["medium"]),
            "ema_slow": self.compute_ema(df, cfg["slow"]),
        }

    # ── MACD ────────────────────────────────────────────────────────────

    def compute_macd(self, df: pd.DataFrame) -> dict[str, pd.Series]:
        """MACD line, signal line, and histogram."""
        cfg = self.cfg["macd"]
        ema_fast = df["close"].ewm(span=cfg["fast"], adjust=False).mean()
        ema_slow = df["close"].ewm(span=cfg["slow"], adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=cfg["signal"], adjust=False).mean()
        histogram = macd_line - signal_line
        logger.debug("MACD computed")
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
        }

    # ── Bollinger Bands ─────────────────────────────────────────────────

    def compute_bollinger_bands(self, df: pd.DataFrame) -> dict[str, pd.Series]:
        """Upper, middle, and lower Bollinger Bands."""
        cfg = self.cfg["bollinger_bands"]
        middle = df["close"].rolling(window=cfg["period"]).mean()
        std = df["close"].rolling(window=cfg["period"]).std()
        upper = middle + cfg["std_dev"] * std
        lower = middle - cfg["std_dev"] * std
        logger.debug("Bollinger Bands computed")
        return {"bb_upper": upper, "bb_middle": middle, "bb_lower": lower}

    # ── ATR ──────────────────────────────────────────────────────────────

    def compute_atr(self, df: pd.DataFrame, period: int | None = None) -> pd.Series:
        """Average True Range."""
        period = period or self.cfg["atr"]["period"]
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        logger.debug("ATR(%d) computed", period)
        return atr

    # ── ADX ──────────────────────────────────────────────────────────────

    def compute_adx(self, df: pd.DataFrame, period: int | None = None) -> pd.Series:
        """Average Directional Index."""
        period = period or self.cfg["adx"]["period"]
        high = df["high"]
        low = df["low"]
        close = df["close"]

        plus_dm = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)

        # Zero out when one DM is not greater than the other
        plus_dm[plus_dm < minus_dm] = 0
        minus_dm[minus_dm < plus_dm] = 0

        atr = self.compute_atr(df, period)
        atr_safe = atr.replace(0, np.nan)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_safe)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_safe)

        dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
        adx = dx.rolling(window=period).mean()
        logger.debug("ADX(%d) computed", period)
        return adx

    # ── Fibonacci Retracement ───────────────────────────────────────────

    def compute_fibonacci_levels(
        self, df: pd.DataFrame, lookback: int = 50
    ) -> dict[str, float]:
        """Auto-compute Fibonacci retracement levels."""
        recent = df.tail(lookback)
        high = recent["high"].max()
        low = recent["low"].min()
        diff = high - low

        levels = {
            "fib_0": high,
            "fib_236": high - 0.236 * diff,
            "fib_382": high - 0.382 * diff,
            "fib_500": high - 0.500 * diff,
            "fib_618": high - 0.618 * diff,
            "fib_786": high - 0.786 * diff,
            "fib_100": low,
        }
        logger.debug("Fibonacci levels: %s", levels)
        return levels

    # ── Support / Resistance (pivot-based) ──────────────────────────────

    def compute_support_resistance(
        self, df: pd.DataFrame, window: int = 20
    ) -> dict[str, list[float]]:
        """Find local support and resistance levels."""
        supports: list[float] = []
        resistances: list[float] = []

        for i in range(window, len(df) - window):
            low_window = df["low"].iloc[i - window : i + window + 1]
            high_window = df["high"].iloc[i - window : i + window + 1]

            if df["low"].iloc[i] == low_window.min():
                supports.append(float(df["low"].iloc[i]))
            if df["high"].iloc[i] == high_window.max():
                resistances.append(float(df["high"].iloc[i]))

        # Deduplicate nearby levels (within 0.5%)
        supports = self._deduplicate_levels(supports)
        resistances = self._deduplicate_levels(resistances)

        logger.debug(
            "Support/Resistance: %d supports, %d resistances",
            len(supports),
            len(resistances),
        )
        return {"supports": supports, "resistances": resistances}

    @staticmethod
    def _deduplicate_levels(levels: list[float], tolerance: float = 0.005) -> list[float]:
        """Merge price levels that are within *tolerance* of each other."""
        if not levels:
            return []
        levels = sorted(set(levels))
        merged: list[float] = [levels[0]]
        for lvl in levels[1:]:
            if (lvl - merged[-1]) / merged[-1] > tolerance:
                merged.append(lvl)
        return merged

    # ── Trend Detection ─────────────────────────────────────────────────

    def detect_trend(self, df: pd.DataFrame) -> str:
        """Return 'UPTREND', 'DOWNTREND', or 'SIDEWAYS'."""
        emas = self.compute_ema_set(df)
        fast = emas["ema_fast"].iloc[-1]
        medium = emas["ema_medium"].iloc[-1]
        slow = emas["ema_slow"].iloc[-1]

        if fast > medium > slow:
            return "UPTREND"
        if fast < medium < slow:
            return "DOWNTREND"
        return "SIDEWAYS"

    # ── Supply / Demand Zones ──────────────────────────────────────────

    def compute_supply_demand_zones(
        self, df: pd.DataFrame, lookback: int = 50, strength: int = 3
    ) -> dict[str, list[dict]]:
        """Detect supply (resistance) and demand (support) zones.

        A *demand zone* forms when a strong bullish candle follows a base
        of narrow-range candles.  A *supply zone* forms on a strong bearish
        candle after a similar base.

        Returns ``{"demand": [...], "supply": [...]}`` where each entry is
        ``{"low": float, "high": float}``.
        """
        demand_zones: list[dict] = []
        supply_zones: list[dict] = []

        recent = df.tail(lookback).reset_index(drop=True)
        body = (recent["close"] - recent["open"]).abs()
        avg_body = body.rolling(20).mean()

        for i in range(strength, len(recent) - 1):
            # Current candle body relative to recent average
            if pd.isna(avg_body.iloc[i]) or avg_body.iloc[i] == 0:
                continue

            ratio = body.iloc[i] / avg_body.iloc[i]

            # Demand zone: strong bullish candle (body > 1.5× average)
            if recent["close"].iloc[i] > recent["open"].iloc[i] and ratio > 1.5:
                base_low = recent["low"].iloc[max(0, i - strength) : i].min()
                base_high = recent["open"].iloc[i]
                demand_zones.append(
                    {"low": float(base_low), "high": float(base_high)}
                )

            # Supply zone: strong bearish candle
            if recent["close"].iloc[i] < recent["open"].iloc[i] and ratio > 1.5:
                base_high = recent["high"].iloc[max(0, i - strength) : i].max()
                base_low = recent["open"].iloc[i]
                supply_zones.append(
                    {"low": float(base_low), "high": float(base_high)}
                )

        logger.debug(
            "Supply/Demand zones: %d demand, %d supply",
            len(demand_zones),
            len(supply_zones),
        )
        return {"demand": demand_zones, "supply": supply_zones}

    # ── Order Block Identification ─────────────────────────────────────

    def compute_order_blocks(
        self, df: pd.DataFrame, lookback: int = 50, min_move_pct: float = 0.01
    ) -> dict[str, list[dict]]:
        """Identify bullish and bearish order blocks.

        An *order block* is the last opposing candle before a strong
        directional move.

        Returns ``{"bullish_ob": [...], "bearish_ob": [...]}``.
        """
        bullish_obs: list[dict] = []
        bearish_obs: list[dict] = []

        recent = df.tail(lookback).reset_index(drop=True)

        for i in range(1, len(recent) - 2):
            curr_close = recent["close"].iloc[i]
            next_close = recent["close"].iloc[i + 1]
            prev_close = recent["close"].iloc[i - 1]

            if curr_close == 0:
                continue

            move_pct = (next_close - curr_close) / curr_close

            # Bullish OB: last bearish candle before a strong up-move
            if (
                recent["close"].iloc[i] < recent["open"].iloc[i]
                and move_pct > min_move_pct
            ):
                bullish_obs.append({
                    "low": float(recent["low"].iloc[i]),
                    "high": float(recent["high"].iloc[i]),
                    "open": float(recent["open"].iloc[i]),
                    "close": float(recent["close"].iloc[i]),
                })

            # Bearish OB: last bullish candle before a strong down-move
            if (
                recent["close"].iloc[i] > recent["open"].iloc[i]
                and move_pct < -min_move_pct
            ):
                bearish_obs.append({
                    "low": float(recent["low"].iloc[i]),
                    "high": float(recent["high"].iloc[i]),
                    "open": float(recent["open"].iloc[i]),
                    "close": float(recent["close"].iloc[i]),
                })

        logger.debug(
            "Order blocks: %d bullish, %d bearish",
            len(bullish_obs),
            len(bearish_obs),
        )
        return {"bullish_ob": bullish_obs, "bearish_ob": bearish_obs}

    # ── All-in-one ─────────────────────────────────────────────────────

    def analyse(self, df: pd.DataFrame) -> dict:
        """Run the full indicator suite and return a summary dict."""
        if df.empty:
            logger.warning("Empty DataFrame – skipping analysis")
            return {}

        rsi = self.compute_rsi(df)
        emas = self.compute_ema_set(df)
        macd = self.compute_macd(df)
        bb = self.compute_bollinger_bands(df)
        atr = self.compute_atr(df)
        adx = self.compute_adx(df)
        fib = self.compute_fibonacci_levels(df)
        sr = self.compute_support_resistance(df)
        sd_zones = self.compute_supply_demand_zones(df)
        order_blocks = self.compute_order_blocks(df)
        trend = self.detect_trend(df)

        result = {
            "rsi": rsi.iloc[-1] if not rsi.empty else None,
            "ema_fast": emas["ema_fast"].iloc[-1],
            "ema_medium": emas["ema_medium"].iloc[-1],
            "ema_slow": emas["ema_slow"].iloc[-1],
            "macd_line": macd["macd_line"].iloc[-1],
            "macd_signal": macd["signal_line"].iloc[-1],
            "macd_histogram": macd["histogram"].iloc[-1],
            "bb_upper": bb["bb_upper"].iloc[-1],
            "bb_middle": bb["bb_middle"].iloc[-1],
            "bb_lower": bb["bb_lower"].iloc[-1],
            "atr": atr.iloc[-1] if not atr.empty else None,
            "adx": adx.iloc[-1] if not adx.empty else None,
            "fibonacci": fib,
            "support_resistance": sr,
            "supply_demand_zones": sd_zones,
            "order_blocks": order_blocks,
            "trend": trend,
            "close": df["close"].iloc[-1],
        }
        logger.info("Analysis complete – trend=%s, RSI=%.1f", trend, result["rsi"] or 0)
        return result
