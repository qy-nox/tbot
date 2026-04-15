"""
On-chain data integration and whale tracking.

Uses free public APIs to monitor:
- Large BTC/ETH transactions (whale movements)
- Exchange inflow/outflow estimates
- Active address trends
- Network hash rate / difficulty
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger("trading_bot.onchain_analyzer")

# ── Free API endpoints ──────────────────────────────────────────────────

BLOCKCHAIN_INFO_URL = "https://blockchain.info"
BLOCKCHAIR_URL = "https://api.blockchair.com"
MEMPOOL_URL = "https://mempool.space/api"


@dataclass
class WhaleAlert:
    """A detected large transaction."""

    tx_hash: str
    asset: str
    amount: float
    usd_value: float
    from_addr: str
    to_addr: str
    timestamp: datetime
    direction: str  # EXCHANGE_INFLOW / EXCHANGE_OUTFLOW / UNKNOWN


@dataclass
class OnChainMetrics:
    """Aggregated on-chain health metrics."""

    active_addresses_24h: Optional[int] = None
    transaction_count_24h: Optional[int] = None
    avg_transaction_value: Optional[float] = None
    hash_rate: Optional[float] = None
    difficulty: Optional[float] = None
    mempool_size: Optional[int] = None
    whale_alerts: list[WhaleAlert] = field(default_factory=list)
    net_exchange_flow: Optional[float] = None  # positive = inflow (bearish)
    sentiment_score: Optional[float] = None  # -1 to 1


class OnChainAnalyzer:
    """Fetch and analyse on-chain data from free public APIs."""

    # Known exchange address prefixes (simplified heuristic)
    EXCHANGE_KEYWORDS = [
        "binance", "coinbase", "kraken", "bitfinex", "huobi",
        "okex", "bybit", "kucoin", "ftx", "gemini",
    ]

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout

    # ── Public interface ────────────────────────────────────────────────

    def get_metrics(self, asset: str = "bitcoin") -> OnChainMetrics:
        """Aggregate on-chain metrics for *asset*."""
        metrics = OnChainMetrics()

        if asset.lower() in ("bitcoin", "btc", "btc/usdt"):
            self._fetch_btc_stats(metrics)
            self._fetch_mempool_stats(metrics)

        self._compute_sentiment(metrics)
        return metrics

    def get_whale_transactions(
        self, asset: str = "bitcoin", min_usd: float = 1_000_000
    ) -> list[WhaleAlert]:
        """Fetch recent large transactions for *asset*.

        Uses free Blockchair API (limited rate).
        """
        whales: list[WhaleAlert] = []

        if asset.lower() in ("bitcoin", "btc", "btc/usdt"):
            whales = self._fetch_btc_large_txs(min_usd)
        elif asset.lower() in ("ethereum", "eth", "eth/usdt"):
            whales = self._fetch_eth_large_txs(min_usd)

        logger.info(
            "Whale scan (%s): %d transactions above $%s",
            asset, len(whales), f"{min_usd:,.0f}",
        )
        return whales

    def analyse_whale_sentiment(self, whales: list[WhaleAlert]) -> float:
        """Return a sentiment score (-1 bearish to +1 bullish) from whale activity.

        Exchange inflows are bearish (selling), outflows are bullish (accumulation).
        """
        if not whales:
            return 0.0

        inflow = sum(w.usd_value for w in whales if w.direction == "EXCHANGE_INFLOW")
        outflow = sum(w.usd_value for w in whales if w.direction == "EXCHANGE_OUTFLOW")
        total = inflow + outflow
        if total == 0:
            return 0.0

        # Outflow-heavy = bullish, inflow-heavy = bearish
        score = (outflow - inflow) / total
        return round(score, 4)

    # ── BTC stats (blockchain.info) ─────────────────────────────────────

    def _fetch_btc_stats(self, metrics: OnChainMetrics) -> None:
        try:
            resp = requests.get(
                f"{BLOCKCHAIN_INFO_URL}/stats",
                params={"format": "json"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            metrics.hash_rate = data.get("hash_rate")
            metrics.difficulty = data.get("difficulty")
            metrics.transaction_count_24h = data.get("n_tx")
            logger.debug("BTC stats fetched: tx=%s", metrics.transaction_count_24h)
        except requests.RequestException as exc:
            logger.warning("Failed to fetch BTC stats: %s", exc)

    # ── Mempool stats ───────────────────────────────────────────────────

    def _fetch_mempool_stats(self, metrics: OnChainMetrics) -> None:
        try:
            resp = requests.get(
                f"{MEMPOOL_URL}/mempool",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            metrics.mempool_size = data.get("count")
            logger.debug("Mempool size: %s", metrics.mempool_size)
        except requests.RequestException as exc:
            logger.warning("Failed to fetch mempool stats: %s", exc)

    # ── BTC large transactions (Blockchair) ─────────────────────────────

    def _fetch_btc_large_txs(self, min_usd: float) -> list[WhaleAlert]:
        """Fetch recent large BTC transactions from Blockchair (free tier)."""
        whales: list[WhaleAlert] = []
        try:
            url = f"{BLOCKCHAIR_URL}/bitcoin/transactions"
            params = {
                "s": "output_total_usd(desc)",
                "limit": 10,
            }
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("data", [])

            for tx in data:
                usd_value = tx.get("output_total_usd", 0)
                if usd_value < min_usd:
                    continue

                whale = WhaleAlert(
                    tx_hash=tx.get("hash", ""),
                    asset="BTC",
                    amount=tx.get("output_total", 0) / 1e8,  # satoshi -> BTC
                    usd_value=usd_value,
                    from_addr=tx.get("input_total", "unknown"),
                    to_addr=tx.get("output_total", "unknown"),
                    timestamp=datetime.now(timezone.utc),
                    direction=self._classify_direction(tx),
                )
                whales.append(whale)

        except requests.RequestException as exc:
            logger.warning("Blockchair BTC query failed: %s", exc)
        return whales

    def _fetch_eth_large_txs(self, min_usd: float) -> list[WhaleAlert]:
        """Fetch recent large ETH transactions from Blockchair (free tier)."""
        whales: list[WhaleAlert] = []
        try:
            url = f"{BLOCKCHAIR_URL}/ethereum/transactions"
            params = {
                "s": "value_usd(desc)",
                "limit": 10,
            }
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("data", [])

            for tx in data:
                usd_value = tx.get("value_usd", 0)
                if usd_value < min_usd:
                    continue

                whale = WhaleAlert(
                    tx_hash=tx.get("hash", ""),
                    asset="ETH",
                    amount=tx.get("value", 0) / 1e18,  # wei -> ETH
                    usd_value=usd_value,
                    from_addr=str(tx.get("sender", "unknown")),
                    to_addr=str(tx.get("recipient", "unknown")),
                    timestamp=datetime.now(timezone.utc),
                    direction=self._classify_direction(tx),
                )
                whales.append(whale)

        except requests.RequestException as exc:
            logger.warning("Blockchair ETH query failed: %s", exc)
        return whales

    # ── Direction classification ────────────────────────────────────────

    def _classify_direction(self, tx: dict) -> str:
        """Heuristic: classify whether tx is an exchange inflow, outflow, or unknown."""
        recipient = str(tx.get("recipient", tx.get("output_total", ""))).lower()
        sender = str(tx.get("sender", tx.get("input_total", ""))).lower()

        for keyword in self.EXCHANGE_KEYWORDS:
            if keyword in recipient:
                return "EXCHANGE_INFLOW"
            if keyword in sender:
                return "EXCHANGE_OUTFLOW"

        return "UNKNOWN"

    # ── Sentiment computation ───────────────────────────────────────────

    @staticmethod
    def _compute_sentiment(metrics: OnChainMetrics) -> None:
        """Derive a simple sentiment score from on-chain metrics."""
        signals: list[float] = []

        # High mempool = congestion = high demand (mildly bullish)
        if metrics.mempool_size is not None:
            if metrics.mempool_size > 50_000:
                signals.append(0.2)
            elif metrics.mempool_size < 5_000:
                signals.append(-0.1)
            else:
                signals.append(0.0)

        # High tx count = network activity (bullish)
        if metrics.transaction_count_24h is not None:
            if metrics.transaction_count_24h > 300_000:
                signals.append(0.3)
            elif metrics.transaction_count_24h < 200_000:
                signals.append(-0.2)
            else:
                signals.append(0.0)

        if signals:
            metrics.sentiment_score = round(sum(signals) / len(signals), 4)
        else:
            metrics.sentiment_score = 0.0
