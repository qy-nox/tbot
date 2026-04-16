"""Advanced sentiment analyzer combining existing sentiment and on-chain proxies."""

from __future__ import annotations

from core.onchain_analyzer import OnChainAnalyzer
from core.sentiment_analyzer import SentimentAnalyzer


class AdvancedSentimentAnalyzer:
    def __init__(self) -> None:
        self.sentiment = SentimentAnalyzer()
        self.onchain = OnChainAnalyzer()

    def analyse(self, pair: str) -> dict:
        s = self.sentiment.analyse(pair)
        oc = self.onchain.analyse(pair)
        score = (s.score + oc.get("composite_score", 0.0)) / 2
        return {"label": s.label, "score": score, "impact": s.impact, "onchain": oc}
