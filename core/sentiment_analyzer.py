"""
Sentiment analysis module.
Combines TextBlob and VADER to score crypto-related news headlines.
"""

import logging
from dataclasses import dataclass, field

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger("trading_bot.sentiment_analyzer")


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
        self.vader = SentimentIntensityAnalyzer()
        self.vader_weight = vader_weight
        self.textblob_weight = textblob_weight
        logger.info(
            "SentimentAnalyzer ready (VADER=%.0f%%, TextBlob=%.0f%%)",
            vader_weight * 100,
            textblob_weight * 100,
        )

    # ── Single headline ─────────────────────────────────────────────────

    def analyse_headline(self, text: str) -> dict:
        """Return individual TextBlob and VADER scores for one headline."""
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
