"""Entry and exit planning engine for spot/futures signals."""

from __future__ import annotations


class EntryExitEngine:
    def entry_signal(self, *, rsi: float, ema20: float, ema50: float, close: float, bb_lower: float, support: float | None = None, resistance: float | None = None) -> tuple[str, list[str]]:
        reasons: list[str] = []
        direction = "HOLD"

        if rsi < 30 and ema20 > ema50:
            direction = "BUY"
            reasons.append(f"RSI oversold ({rsi:.1f}) + EMA confirmation")
        if close <= bb_lower:
            direction = "BUY"
            reasons.append("Bollinger lower band touch")
        if support is not None and abs(close - support) / max(close, 1e-9) <= 0.01:
            direction = "BUY"
            reasons.append("Support bounce")
        if resistance is not None and close > resistance:
            direction = "BUY"
            reasons.append("Breakout above resistance")

        return direction, reasons

    def build_targets(self, entry: float, stop_loss: float, direction: str) -> dict[str, float]:
        risk = abs(entry - stop_loss)
        if direction == "BUY":
            return {
                "tp1": round(entry + risk * 2.0, 8),
                "tp2": round(entry + risk * 2.5, 8),
                "tp3": round(entry + risk * 3.0, 8),
            }
        return {
            "tp1": round(entry - risk * 2.0, 8),
            "tp2": round(entry - risk * 2.5, 8),
            "tp3": round(entry - risk * 3.0, 8),
        }

    def should_exit(self, *, close: float, direction: str, stop_loss: float, targets: dict[str, float], divergence: str = "NONE", trend_reversal: bool = False, time_expired: bool = False) -> tuple[bool, str]:
        if direction == "BUY":
            if close <= stop_loss:
                return True, "stop_loss_hit"
            if close >= targets.get("tp3", float("inf")):
                return True, "tp3_hit"
        elif direction == "SELL":
            if close >= stop_loss:
                return True, "stop_loss_hit"
            if close <= targets.get("tp3", float("-inf")):
                return True, "tp3_hit"

        if divergence in {"BULLISH", "BEARISH"}:
            return True, "divergence"
        if trend_reversal:
            return True, "trend_reversal"
        if time_expired:
            return True, "time_exit"
        return False, "hold"
