"""Signal payload generator using required professional JSON format."""

from __future__ import annotations

from datetime import datetime, timezone


class SignalGenerator:
    def build_signal(
        self,
        *,
        pair: str,
        timeframe: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        tp1: float,
        tp2: float,
        tp3: float,
        confidence: int,
        explanation: str,
        indicators: list[str],
        pattern: str,
        exchange: str = "Binance",
        validity_minutes: int = 120,
    ) -> dict:
        entry_delta = abs(entry_price) * 0.02
        risk = abs(entry_price - stop_loss)
        reward = abs(tp3 - entry_price)
        risk_reward_ratio = "1:0"
        if risk > 0:
            rr_value = round(reward / risk, 2)
            rr_text = str(int(rr_value)) if rr_value.is_integer() else str(rr_value)
            risk_reward_ratio = f"1:{rr_text}"
        return {
            "pair": pair,
            "timeframe": timeframe,
            "direction": direction,
            "entry_zone": {
                "min": round(entry_price - entry_delta, 8),
                "max": round(entry_price + entry_delta, 8),
            },
            "targets": {
                "tp1": round(tp1, 8),
                "tp2": round(tp2, 8),
                "tp3": round(tp3, 8),
            },
            "stop_loss": round(stop_loss, 8),
            "risk_reward_ratio": risk_reward_ratio,
            "confidence": int(confidence),
            "explanation": explanation,
            "indicators": indicators,
            "pattern": pattern,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "validity_minutes": int(validity_minutes),
            "exchange": exchange,
        }
