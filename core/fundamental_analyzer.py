"""Fundamental and economic-event utilities for signal filtering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class EconomicEvent:
    name: str
    timestamp: datetime
    impact: str
    forecast: float | None = None
    actual: float | None = None
    previous: float | None = None


class FundamentalAnalyzer:
    HIGH_IMPACT_EVENTS = {"CPI", "FOMC", "NFP", "INTEREST_RATE", "GDP", "INFLATION"}

    def classify_event_impact(self, event_name: str) -> str:
        normalized = event_name.upper().replace(" ", "_")
        return "HIGH" if any(key in normalized for key in self.HIGH_IMPACT_EVENTS) else "MEDIUM"

    def parse_events(self, items: list[dict]) -> list[EconomicEvent]:
        events: list[EconomicEvent] = []
        for item in items:
            raw_ts = item.get("timestamp")
            if isinstance(raw_ts, datetime):
                ts = raw_ts.astimezone(timezone.utc)
            else:
                ts = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00")).astimezone(timezone.utc)
            name = item.get("name", "UNKNOWN")
            events.append(
                EconomicEvent(
                    name=name,
                    timestamp=ts,
                    impact=item.get("impact", self.classify_event_impact(name)),
                    forecast=item.get("forecast"),
                    actual=item.get("actual"),
                    previous=item.get("previous"),
                )
            )
        return events

    def should_pause_trading(self, now: datetime, events: list[EconomicEvent], window_minutes: int = 30) -> tuple[bool, str]:
        now_utc = now.astimezone(timezone.utc)
        window = timedelta(minutes=window_minutes)
        for event in events:
            if event.impact.upper() != "HIGH":
                continue
            if event.timestamp - window <= now_utc <= event.timestamp + window:
                return True, f"High-impact event window: {event.name}"
        return False, ""

    def risk_adjustment(self, now: datetime, events: list[EconomicEvent]) -> dict[str, float | bool | str]:
        paused, reason = self.should_pause_trading(now, events)
        if paused:
            return {"allow_signals": False, "stop_multiplier": 0.0, "reason": reason}

        for event in events:
            if event.impact.upper() == "MEDIUM" and abs((event.timestamp - now.astimezone(timezone.utc)).total_seconds()) <= 1800:
                return {"allow_signals": True, "stop_multiplier": 1.25, "reason": f"Medium-impact event: {event.name}"}
        return {"allow_signals": True, "stop_multiplier": 1.0, "reason": "normal"}
