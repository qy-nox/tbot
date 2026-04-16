"""Market data helpers for the main signal bot."""

from __future__ import annotations

from typing import Any

import requests

_BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"
_DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT")


def _normalize_symbol(symbol: str) -> str:
    return symbol.replace("USDT", "")


def get_live_market_status(symbols: tuple[str, ...] = _DEFAULT_SYMBOLS) -> dict[str, Any]:
    market: dict[str, dict[str, float | str]] = {}
    bullish = 0
    bearish = 0

    for symbol in symbols:
        try:
            response = requests.get(_BINANCE_URL, params={"symbol": symbol}, timeout=5)
            response.raise_for_status()
            data = response.json()
            price = float(data.get("lastPrice", 0.0))
            change_24h = float(data.get("priceChangePercent", 0.0))
        except Exception:
            price = 0.0
            change_24h = 0.0

        if change_24h >= 0:
            bullish += 1
        else:
            bearish += 1

        market[_normalize_symbol(symbol)] = {
            "price": round(price, 2),
            "change_24h": round(change_24h, 2),
            "status": "up" if change_24h >= 0 else "down",
        }

    trend = "Bullish" if bullish >= bearish else "Bearish"
    return {"assets": market, "trend": trend}
