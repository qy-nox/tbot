"""Instant market data helpers with websocket reconnect support."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

import aiohttp

logger = logging.getLogger(__name__)

TickerCallback = Callable[[dict[str, object]], Awaitable[None]]


class BinanceMarketData:
    """Simple Binance stream client with automatic reconnection."""

    STREAM_URL = "wss://stream.binance.com:9443/ws/!ticker@arr"

    def __init__(self, reconnect_delay: float = 1.0, heartbeat: float = 30.0) -> None:
        self.reconnect_delay = reconnect_delay
        self.heartbeat = heartbeat
        self._running = False

    async def stream(self, callback: TickerCallback) -> None:
        """Stream ticker updates and invoke *callback* for each payload."""
        self._running = True
        async with aiohttp.ClientSession() as session:
            while self._running:
                try:
                    async with session.ws_connect(self.STREAM_URL, heartbeat=self.heartbeat) as ws:
                        async for message in ws:
                            if message.type != aiohttp.WSMsgType.TEXT:
                                continue
                            try:
                                data = json.loads(message.data)
                            except json.JSONDecodeError:
                                logger.warning("Invalid websocket payload: %r", message.data[:200])
                                continue
                            if isinstance(data, list):
                                for item in data:
                                    await callback(item)
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    logger.warning("Binance websocket reconnect after error: %s", exc)
                    await asyncio.sleep(self.reconnect_delay)

    def stop(self) -> None:
        """Request stream shutdown."""
        self._running = False
