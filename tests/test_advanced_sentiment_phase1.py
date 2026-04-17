import unittest

from core.advanced_sentiment import AdvancedSentiment
from core.fear_greed_index import FearGreedReading
from core.news_aggregator import NewsAggregator
from core.sentiment_consensus import SentimentConsensusScorer, SourceSentiment


class _FakeFearGreed:
    def fetch(self):
        from datetime import datetime, timezone

        return FearGreedReading(value=70, classification="Greed", timestamp=datetime.now(timezone.utc))


class _FakeSentimentAnalyzer:
    def analyse_headline(self, text: str) -> dict:
        score = 0.6 if "up" in text.lower() else -0.4
        return {"combined": score}


class AdvancedSentimentPhase1Tests(unittest.TestCase):
    def test_consensus_weights_are_applied(self):
        scorer = SentimentConsensusScorer()
        result = scorer.calculate(
            [
                SourceSentiment(name="a", score=1.0, weight=2.0),
                SourceSentiment(name="b", score=-1.0, weight=1.0),
            ]
        )
        self.assertGreater(result.score, 0.0)
        self.assertEqual(result.label, "BULLISH")

    def test_news_aggregator_deduplicates_items(self):
        aggregator = NewsAggregator()
        providers = {
            "alpha": lambda: [
                {"title": "BTC up today", "url": "https://a"},
                {"title": "BTC up today", "url": "https://a"},
            ]
        }
        items = aggregator.aggregate(providers=providers)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "alpha")

    def test_advanced_sentiment_aggregates_news_and_fear_greed(self):
        aggregator = NewsAggregator()
        providers = {
            "news": lambda: [
                {"title": "BTC up after strong inflows", "url": "https://x"},
            ]
        }
        engine = AdvancedSentiment(
            news_aggregator=aggregator,
            fear_greed_index=_FakeFearGreed(),
            sentiment_analyzer=_FakeSentimentAnalyzer(),
        )

        result = engine.analyze(providers=providers)
        self.assertIn(result["label"], {"BULLISH", "NEUTRAL", "BEARISH"})
        self.assertEqual(result["news_items_analyzed"], 1)
        self.assertEqual(result["fear_greed_value"], 70)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)


if __name__ == "__main__":
    unittest.main()
