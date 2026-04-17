"""Fear & Greed index helper with safe defaults."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from json import loads
from urllib.request import urlopen


@dataclass
class FearGreedReading:
    value: int
    classification: str
    timestamp: datetime
    source: str = "alternative.me"


class FearGreedIndex:
    API_URL = "https://api.alternative.me/fng/?limit=1&format=json"

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    def fetch(self) -> FearGreedReading:
        try:
            with urlopen(self.API_URL, timeout=self.timeout_seconds) as response:
                payload = loads(response.read().decode("utf-8"))
            item = (payload.get("data") or [{}])[0]
            value = int(item.get("value", 50))
            timestamp_value = item.get("timestamp")
            if timestamp_value:
                timestamp = datetime.fromtimestamp(int(timestamp_value), tz=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            return FearGreedReading(
                value=max(0, min(100, value)),
                classification=str(item.get("value_classification", "Neutral")),
                timestamp=timestamp,
            )
        except Exception:
            return FearGreedReading(
                value=50,
                classification="Neutral",
                timestamp=datetime.now(timezone.utc),
            )

    def get_index(self) -> FearGreedReading:
        return self.fetch()
