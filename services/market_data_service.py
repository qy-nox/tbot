"""Market data service entrypoints."""

from __future__ import annotations

from bots.main_signal_bot.market_data import BinanceMarketData


def create_stream_client() -> BinanceMarketData:
    return BinanceMarketData()
