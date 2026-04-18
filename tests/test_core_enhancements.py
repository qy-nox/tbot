import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd

from core.data_fetcher import DataFetcher
from core.sentiment_analyzer import SentimentAnalyzer
from core.technical_analyzer import TechnicalAnalyzer


class _FakeExchange:
    def __init__(self, rows):
        self.rows = rows

    def fetch_ohlcv(self, symbol, timeframe, limit):
        return self.rows


class _TestFetcher(DataFetcher):
    def __init__(self, rows):
        self._rows = rows
        super().__init__()

    def _init_exchange(self):
        return _FakeExchange(self._rows)


class CoreEnhancementsTests(unittest.TestCase):
    def test_data_fetcher_rejects_invalid_numeric_rows(self):
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        rows = [
            [now_ms, 100, 102, 99, 101, 10],
            [now_ms + 60_000, 101, 103, 100, 102, -5],
        ]
        fetcher = _TestFetcher(rows)
        result = fetcher.fetch_ohlcv("BTC/USDT", timeframe="1m", limit=2)
        self.assertTrue(result.empty)

    def test_data_fetcher_rejects_nonfinite_and_inverted_candles(self):
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        nan_rows = [
            [now_ms, 100, 102, 99, 101, 10],
            [now_ms + 60_000, 101, 103, 100, float("nan"), 8],
        ]
        inverted_rows = [
            [now_ms, 100, 102, 99, 101, 10],
            [now_ms + 60_000, 101, 98, 100, 101, 8],
        ]
        self.assertTrue(_TestFetcher(nan_rows).fetch_ohlcv("BTC/USDT", timeframe="1m", limit=2).empty)
        self.assertTrue(_TestFetcher(inverted_rows).fetch_ohlcv("BTC/USDT", timeframe="1m", limit=2).empty)

    def test_technical_analysis_adds_new_safety_outputs(self):
        base = {
            "open": [100 + i for i in range(90)],
            "high": [101 + i for i in range(90)],
            "low": [99 + i for i in range(90)],
            "close": [100 + i for i in range(90)],
            "volume": [1_000 + i for i in range(90)],
        }
        result = TechnicalAnalyzer().analyse(pd.DataFrame(base))
        self.assertIn("ichimoku", result)
        self.assertIn("anomaly_detection", result)
        self.assertIn("signal_confidence", result)
        self.assertGreaterEqual(result["signal_confidence"], 0)
        self.assertLessEqual(result["signal_confidence"], 100)

    @patch("core.sentiment_analyzer.requests.get")
    def test_sentiment_newsapi_and_multisource_are_additive(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "articles": [
                {"title": "Bitcoin rallies as demand rises"},
                {"title": "Market turns bearish after macro pressure"},
            ]
        }

        analyzer = SentimentAnalyzer()
        analyzer.newsapi_key = "dummy"
        newsapi_result = analyzer.analyse_newsapi(query="bitcoin", page_size=5)
        self.assertGreater(newsapi_result.headlines_analysed, 0)

        combined = analyzer.analyse_multi_source(
            {
                "newsapi": [{"title": "Bitcoin rises strongly"}],
                "social": ["Bitcoin drops on profit taking"],
            },
            source_weights={"newsapi": 2.0, "social": 1.0},
        )
        self.assertIn(combined.label, {"BULLISH", "NEUTRAL", "BEARISH"})
        self.assertGreaterEqual(combined.headlines_analysed, 2)


if __name__ == "__main__":
    unittest.main()
