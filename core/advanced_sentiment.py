"""Multi-source advanced sentiment orchestration."""

from __future__ import annotations

from typing import Any

from core.fear_greed_index import FearGreedIndex
from core.news_aggregator import NewsAggregator
from core.sentiment_consensus import SentimentConsensusScorer, SourceSentiment


class _FallbackSentimentAnalyzer:
    def analyse_headline(self, text: str) -> dict:
        lowered = text.lower()
        bullish_terms = ("up", "surge", "rally", "bull")
        bearish_terms = ("down", "drop", "crash", "bear")
        score = 0.0
        if any(term in lowered for term in bullish_terms):
            score += 0.4
        if any(term in lowered for term in bearish_terms):
            score -= 0.4
        return {"combined": score}


def _build_default_sentiment_analyzer() -> Any:
    try:
        from core.sentiment_analyzer import SentimentAnalyzer

        return SentimentAnalyzer()
    except Exception:
        return _FallbackSentimentAnalyzer()


class AdvancedSentiment:
    """Aggregate headline sentiment and fear/greed into a consensus view."""

    def __init__(
        self,
        news_aggregator: NewsAggregator | None = None,
        consensus: SentimentConsensusScorer | None = None,
        fear_greed_index: FearGreedIndex | None = None,
        sentiment_analyzer: Any | None = None,
        fear_greed_weight: float = 0.8,
    ):
        self.news_aggregator = news_aggregator or NewsAggregator()
        self.consensus = consensus or SentimentConsensusScorer()
        self.fear_greed_index = fear_greed_index or FearGreedIndex()
        self.sentiment_analyzer = sentiment_analyzer or _build_default_sentiment_analyzer()
        self.fear_greed_weight = max(0.0, float(fear_greed_weight))

    def analyze(self, providers: dict | None = None) -> dict:
        news_items = self.news_aggregator.aggregate(providers=providers)
        sources: list[SourceSentiment] = []

        for item in news_items:
            headline_score = self._analyze_headline(item.title)
            sources.append(
                SourceSentiment(
                    name=item.source,
                    score=float(headline_score.get("combined", 0.0)),
                    weight=1.0,
                    metadata={"title": item.title, "url": item.url},
                )
            )

        fear_greed = self.fear_greed_index.fetch()
        fear_greed_score = (fear_greed.value - 50.0) / 50.0
        sources.append(
            SourceSentiment(
                name="fear_greed",
                score=fear_greed_score,
                weight=self.fear_greed_weight,
                metadata={
                    "value": fear_greed.value,
                    "classification": fear_greed.classification,
                    "source": fear_greed.source,
                },
            )
        )

        consensus = self.consensus.calculate(sources)
        return {
            "label": consensus.label,
            "score": consensus.score,
            "confidence": consensus.confidence,
            "sources": [
                {
                    "name": source.name,
                    "score": source.score,
                    "weight": source.weight,
                    "metadata": source.metadata,
                }
                for source in consensus.contributions
            ],
            "news_items_analyzed": len(news_items),
            "fear_greed_value": fear_greed.value,
        }

    def analyse(self, providers: dict | None = None) -> dict:
        """Compatibility alias for British spelling."""
        return self.analyze(providers=providers)

    def _analyze_headline(self, headline: str) -> dict:
        analyze_fn = getattr(self.sentiment_analyzer, "analyze_headline", None)
        if callable(analyze_fn):
            return analyze_fn(headline)

        analyse_fn = getattr(self.sentiment_analyzer, "analyse_headline", None)
        if callable(analyse_fn):
            return analyse_fn(headline)

        return _FallbackSentimentAnalyzer().analyse_headline(headline)


class AdvancedSentimentAnalyzer(AdvancedSentiment):
    """Compatibility alias for existing naming conventions."""
