"""Market data helpers for the main signal bot."""

from __future__ import annotations

import logging

import ccxt

from config.settings import Settings

logger = logging.getLogger(__name__)


def get_live_market_status() -> dict:
    """Get real market prices from Binance."""
    try:
        exchange = ccxt.binance(
            {
                "apiKey": Settings.BINANCE_API_KEY or None,
                "secret": Settings.BINANCE_API_SECRET or None,
                "enableRateLimit": True,
            }
        )
        btc = exchange.fetch_ticker("BTC/USDT")
        eth = exchange.fetch_ticker("ETH/USDT")
        bnb = exchange.fetch_ticker("BNB/USDT")

        return {
            "assets": {
                "BTC": {"price": f"${btc['last']:,.2f}", "change": f"{btc['percentage']:+.2f}%"},
                "ETH": {"price": f"${eth['last']:,.2f}", "change": f"{eth['percentage']:+.2f}%"},
                "BNB": {"price": f"${bnb['last']:,.2f}", "change": f"{bnb['percentage']:+.2f}%"},
            },
            "trend": "BULLISH" if btc["last"] > btc["open"] else "BEARISH",
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Market data error: %s", exc)
        return {"assets": {}, "trend": "UNKNOWN"}
