"""Advanced sentiment analyzer combining existing sentiment and on-chain proxies."""

from __future__ import annotations

from core.onchain_analyzer import OnChainAnalyzer
from core.sentiment_analyzer import SentimentAnalyzer


class AdvancedSentimentAnalyzer:
    def __init__(self) -> None:
        self.sentiment = SentimentAnalyzer()
        self.onchain = OnChainAnalyzer()

    def analyse(self, pair: str) -> dict:
        s = self.sentiment.analyse_headlines([pair])
        oc_metrics = self.onchain.get_metrics(pair)
        onchain_score = (
            oc_metrics.sentiment_score
            if oc_metrics.sentiment_score is not None
            else 0.0
        )
        score = (float(s.combined_score) + onchain_score) / 2
        return {
            "label": s.label,
            "score": score,
            "impact": s.impact,
            "onchain": {
                "sentiment_score": onchain_score,
                "active_addresses_24h": oc_metrics.active_addresses_24h,
                "transaction_count_24h": oc_metrics.transaction_count_24h,
                "mempool_size": oc_metrics.mempool_size,
            },
        }
