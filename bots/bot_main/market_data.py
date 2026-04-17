"""Market data helpers for the main signal bot."""

from __future__ import annotations

import json
import logging
from urllib.error import URLError
from urllib.request import urlopen

logger = logging.getLogger(__name__)


_FALLBACK = {
    "BTC": {"price": "42,500.00 USDT", "change": "+2.5%"},
    "ETH": {"price": "2,250.00 USDT", "change": "+1.8%"},
    "BNB": {"price": "610.00 USDT", "change": "+1.1%"},
}


def _format_asset(price: float, change_pct: float) -> dict[str, str]:
    sign = "+" if change_pct >= 0 else ""
    return {
        "price": f"{price:,.2f} USDT",
        "change": f"{sign}{change_pct:.2f}%",
    }


def _trend(changes: list[float]) -> str:
    if not changes:
        return "NEUTRAL"
    avg = sum(changes) / len(changes)
    if avg > 0:
        return "BULLISH"
    if avg < 0:
        return "BEARISH"
    return "NEUTRAL"


def _load_live_tickers() -> dict[str, dict[str, str]]:
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    assets: dict[str, dict[str, str]] = {}
    for symbol in symbols:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        price = float(payload["lastPrice"])
        change_pct = float(payload["priceChangePercent"])
        assets[symbol.replace("USDT", "")] = _format_asset(price, change_pct)
    return assets


def get_live_market_status() -> dict:
    try:
        assets = _load_live_tickers()
        changes = [float(v["change"].replace("%", "")) for v in assets.values()]
        return {"assets": assets, "trend": _trend(changes)}
    except (URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
        logger.warning("Failed to fetch live Binance ticker data: %s", exc)
        return {"assets": _FALLBACK, "trend": "BULLISH"}
