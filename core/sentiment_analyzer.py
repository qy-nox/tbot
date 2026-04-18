"""
Sentiment analysis module.
Combines TextBlob and VADER to score crypto-related news headlines.
"""

import logging
import statistics
import threading
import time
from dataclasses import dataclass, field

import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config.settings import Settings

logger = logging.getLogger("trading_bot.sentiment_analyzer")
NEWSAPI_MAX_RETRY_DELAY_SECONDS = 15.0
CONFLICT_SCALE_FACTOR = 0.25
MAX_CONFLICT_PENALTY = 0.35


@dataclass
class SentimentResult:
    """Aggregated sentiment result for a batch of headlines."""

    textblob_score: float = 0.0
    vader_score: float = 0.0
    combined_score: float = 0.0
    label: str = "NEUTRAL"  # BULLISH / BEARISH / NEUTRAL
    impact: str = "LOW"  # HIGH / MEDIUM / LOW
    headlines_analysed: int = 0
    details: list[dict] = field(default_factory=list)


class SentimentAnalyzer:
    """Analyse sentiment of news headlines using TextBlob + VADER."""

    def __init__(self, vader_weight: float = 0.6, textblob_weight: float = 0.4):
        total_weight = vader_weight + textblob_weight
        if total_weight <= 0:
            logger.warning("Invalid sentiment model weights; falling back to defaults")
            vader_weight, textblob_weight = 0.6, 0.4
            total_weight = vader_weight + textblob_weight
        self.vader = SentimentIntensityAnalyzer()
        self.vader_weight = vader_weight / total_weight
        self.textblob_weight = textblob_weight / total_weight
        self.newsapi_key = Settings.NEWSAPI_KEY
        self._news_cache: dict[str, tuple[float, list[dict]]] = {}
        self._cache_lock = threading.Lock()
        logger.info(
            "SentimentAnalyzer ready (VADER=%.0f%%, TextBlob=%.0f%%)",
            self.vader_weight * 100,
            self.textblob_weight * 100,
        )

    # ── Single headline ─────────────────────────────────────────────────

    def analyse_headline(self, text: str) -> dict:
        """Return individual TextBlob and VADER scores for one headline."""
        if not isinstance(text, str) or not text.strip():
            return {"text": "", "textblob": 0.0, "vader": 0.0, "combined": 0.0}
        tb = TextBlob(text)
        tb_polarity = tb.sentiment.polarity  # -1 … +1

        vader_scores = self.vader.polarity_scores(text)
        vader_compound = vader_scores["compound"]  # -1 … +1

        combined = (
            self.vader_weight * vader_compound
            + self.textblob_weight * tb_polarity
        )
        return {
            "text": text,
            "textblob": tb_polarity,
            "vader": vader_compound,
            "combined": combined,
        }

    # ── Batch analysis ──────────────────────────────────────────────────

    def analyse_headlines(self, headlines: list[str]) -> SentimentResult:
        """Aggregate sentiment across multiple headlines."""
        if not headlines:
            logger.debug("No headlines to analyse")
            return SentimentResult()

        details: list[dict] = []
        tb_total = 0.0
        vd_total = 0.0

        for headline in headlines:
            result = self.analyse_headline(headline)
            details.append(result)
            tb_total += result["textblob"]
            vd_total += result["vader"]

        n = len(headlines)
        avg_tb = tb_total / n
        avg_vd = vd_total / n
        combined = self.vader_weight * avg_vd + self.textblob_weight * avg_tb

        label = self._label(combined)
        impact = self._impact(abs(combined))

        logger.info(
            "Sentiment: %s (score=%.3f, impact=%s, n=%d)",
            label,
            combined,
            impact,
            n,
        )
        return SentimentResult(
            textblob_score=avg_tb,
            vader_score=avg_vd,
            combined_score=combined,
            label=label,
            impact=impact,
            headlines_analysed=n,
            details=details,
        )

    # ── From articles (list of dicts with a 'headline' key) ────────────

    def analyse_articles(self, articles: list[dict]) -> SentimentResult:
        """Extract headlines from article dicts and analyse."""
        headlines = [a.get("headline", a.get("title", "")) for a in articles if a]
        headlines = [h for h in headlines if h]
        return self.analyse_headlines(headlines)

    def analyse_newsapi(self, query: str = "crypto", language: str = "en", page_size: int = 20) -> SentimentResult:
        """Fetch and analyse NewsAPI headlines if API key is configured."""
        articles = self._fetch_newsapi_articles(query=query, language=language, page_size=page_size)
        return self.analyse_articles(articles)

    def analyse_multi_source(
        self,
        sources: dict[str, list[str] | list[dict]],
        source_weights: dict[str, float] | None = None,
    ) -> SentimentResult:
        """Aggregate sentiment from multiple sources with weighted conflict handling."""
        if not sources:
            return SentimentResult()

        source_weights = source_weights or {}
        weighted_total = 0.0
        weight_sum = 0.0
        source_scores: list[float] = []
        total_headlines = 0
        details: list[dict] = []

        for source_name, source_items in sources.items():
            headlines = self._extract_headlines(source_items)
            result = self.analyse_headlines(headlines)
            weight = float(source_weights.get(source_name, 1.0))
            if weight <= 0:
                continue
            weighted_total += result.combined_score * weight
            weight_sum += weight
            source_scores.append(result.combined_score)
            total_headlines += result.headlines_analysed
            details.append(
                {
                    "source": source_name,
                    "weight": weight,
                    "score": result.combined_score,
                    "label": result.label,
                    "headlines": result.headlines_analysed,
                }
            )

        if weight_sum <= 0:
            return SentimentResult(details=details)

        combined = weighted_total / weight_sum
        conflict_penalty = self._conflict_penalty(source_scores)
        adjusted_score = combined * (1.0 - conflict_penalty)
        return SentimentResult(
            textblob_score=0.0,
            vader_score=0.0,
            combined_score=adjusted_score,
            label=self._label(adjusted_score),
            impact=self._impact(abs(adjusted_score)),
            headlines_analysed=total_headlines,
            details=details,
        )

    def _fetch_newsapi_articles(self, query: str, language: str, page_size: int) -> list[dict]:
        if not self.newsapi_key:
            logger.debug("NEWSAPI_KEY missing; skipping NewsAPI sentiment fetch")
            return []

        safe_page_size = max(1, min(int(page_size), 100))
        cache_key = f"{query}|{language}|{safe_page_size}"
        with self._cache_lock:
            cached = self._news_cache.get(cache_key)
            if cached and (time.time() - cached[0]) <= 120:
                return cached[1]

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": safe_page_size,
            "apiKey": self.newsapi_key,
        }
        for attempt in range(1, Settings.EXCHANGE_RETRY_ATTEMPTS + 1):
            try:
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                articles = data.get("articles", []) if isinstance(data, dict) else []
                if isinstance(articles, list):
                    with self._cache_lock:
                        self._news_cache[cache_key] = (time.time(), articles)
                    return articles
                return []
            except (requests.RequestException, ValueError) as exc:
                if attempt >= Settings.EXCHANGE_RETRY_ATTEMPTS:
                    logger.warning("NewsAPI fetch failed: %s", exc)
                    return []
                delay = min(
                    Settings.EXCHANGE_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)),
                    NEWSAPI_MAX_RETRY_DELAY_SECONDS,
                )
                time.sleep(delay)
        return []

    @staticmethod
    def _extract_headlines(source_items: list[str] | list[dict]) -> list[str]:
        headlines: list[str] = []
        for item in source_items:
            if isinstance(item, str):
                value = item.strip()
                if value:
                    headlines.append(value)
                continue
            if isinstance(item, dict):
                value = str(item.get("headline") or item.get("title") or "").strip()
                if value:
                    headlines.append(value)
        return headlines

    @staticmethod
    def _conflict_penalty(source_scores: list[float]) -> float:
        if not source_scores:
            return 0.0
        if len(source_scores) <= 1:
            return 0.0
        dispersion = statistics.pstdev(source_scores)
        return max(0.0, min(dispersion * CONFLICT_SCALE_FACTOR, MAX_CONFLICT_PENALTY))

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _label(score: float) -> str:
        if score > 0.15:
            return "BULLISH"
        if score < -0.15:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _impact(abs_score: float) -> str:
        if abs_score > 0.5:
            return "HIGH"
        if abs_score > 0.25:
            return "MEDIUM"
        return "LOW"
