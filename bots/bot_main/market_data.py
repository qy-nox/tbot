"""Market data helpers for the main signal bot."""

from __future__ import annotations


def get_live_market_status() -> dict:
    return {
        "assets": {
            "BTC": {"price": "42,500 USDT", "change": "+2.5%"},
            "ETH": {"price": "2,250 USDT", "change": "+1.8%"},
        },
        "trend": "BULLISH",
    }
