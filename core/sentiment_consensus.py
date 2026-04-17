"""Weighted sentiment consensus scoring utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class SourceSentiment:
    name: str
    score: float
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class SentimentConsensus:
    score: float
    label: str
    confidence: float
    contributions: list[SourceSentiment]


class SentimentConsensusScorer:
    """Compute a weighted consensus score from multiple sentiment sources."""

    def __init__(self, bullish_threshold: float = 0.2, bearish_threshold: float = -0.2):
        self.bullish_threshold = bullish_threshold
        self.bearish_threshold = bearish_threshold

    def calculate(self, sources: Iterable[SourceSentiment | dict]) -> SentimentConsensus:
        normalized: list[SourceSentiment] = []
        for source in sources:
            if isinstance(source, SourceSentiment):
                item = source
            else:
                item = SourceSentiment(**source)
            if item.weight <= 0:
                continue
            item.score = max(-1.0, min(1.0, float(item.score)))
            normalized.append(item)

        if not normalized:
            return SentimentConsensus(
                score=0.0,
                label="NEUTRAL",
                confidence=0.0,
                contributions=[],
            )

        total_weight = sum(item.weight for item in normalized)
        score = sum(item.score * item.weight for item in normalized) / total_weight
        magnitude = sum(abs(item.score) * item.weight for item in normalized) / total_weight
        confidence = max(0.0, min(1.0, magnitude))

        if score >= self.bullish_threshold:
            label = "BULLISH"
        elif score <= self.bearish_threshold:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        return SentimentConsensus(
            score=score,
            label=label,
            confidence=confidence,
            contributions=normalized,
        )

