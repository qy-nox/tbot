"""
Economic calendar module – RHIC (Risk / High-Impact Calendar).

Fetches upcoming high-impact economic events from Finnhub and provides
a "news blackout" check so the bot avoids entering trades during
market-moving announcements.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger("trading_bot.economic_calendar")

# Finnhub economic-calendar endpoint
_FINNHUB_CALENDAR_URL = "https://finnhub.io/api/v1/calendar/economic"
_CACHE_TTL_SECONDS = 300  # 5 minutes


class EconomicCalendar:
    """Fetch and evaluate upcoming high-impact economic events.

    The primary use-case is to block new signal entries in the minutes
    surrounding a scheduled high-impact event (e.g. FOMC, NFP, CPI).
    This is what the problem statement calls *RHIC* logic:
    **R**isk / **H**igh-**I**mpact **C**alendar blackout.
    """

    def __init__(
        self,
        finnhub_key: str = "",
        skip_minutes: int = 30,
        cache_ttl: int = _CACHE_TTL_SECONDS,
    ) -> None:
        self.finnhub_key = finnhub_key
        self.skip_minutes = skip_minutes
        self._cache_ttl = cache_ttl
        self._cache: list[dict] | None = None
        self._cache_ts: float = 0.0
        self._lock = threading.Lock()

    # ── Public API ─────────────────────────────────────────────────────

    def fetch_events(self, force: bool = False) -> list[dict]:
        """Return a list of upcoming economic events.

        Each event dict contains at minimum::

            {
                "datetime": "<ISO-8601 string>",
                "event":    "<event description>",
                "impact":   "high" | "medium" | "low" | "",
                "currency": "<currency code>",
            }

        Results are cached for ``cache_ttl`` seconds to avoid hammering
        the Finnhub API on every scan cycle.
        """
        with self._lock:
            if not force and self._cache is not None:
                age = time.time() - self._cache_ts
                if age < self._cache_ttl:
                    return list(self._cache)

            events = self._fetch_from_finnhub()
            self._cache = events
            self._cache_ts = time.time()
            return list(events)

    def is_high_impact_window(self, currencies: list[str] | None = None) -> bool:
        """Return True when we are within *skip_minutes* of a high-impact event.

        Parameters
        ----------
        currencies:
            Optional list of currency codes to filter events (e.g. ``["USD"]``).
            When *None* or empty, all currencies are considered.
        """
        try:
            events = self.fetch_events()
        except Exception:
            logger.warning("EconomicCalendar: failed to fetch events – allowing trade", exc_info=True)
            return False

        now = datetime.now(timezone.utc)
        window = timedelta(minutes=max(0, self.skip_minutes))

        for event in events:
            if not self._is_high_impact(event):
                continue

            # Currency filter
            if currencies:
                event_currency = str(event.get("currency", "")).upper()
                if event_currency not in [c.upper() for c in currencies]:
                    continue

            event_time = self._parse_event_time(event)
            if event_time is None:
                continue

            # Block if event is within the window (before or after)
            if abs((event_time - now).total_seconds()) <= window.total_seconds():
                logger.info(
                    "RHIC blackout: high-impact event '%s' (%s) at %s – skipping trade",
                    event.get("event", "unknown"),
                    event.get("currency", ""),
                    event_time.isoformat(),
                )
                return True

        return False

    def upcoming_high_impact(
        self, hours_ahead: int = 24, currencies: list[str] | None = None
    ) -> list[dict]:
        """Return high-impact events occurring within the next *hours_ahead* hours."""
        try:
            events = self.fetch_events()
        except Exception:
            logger.warning("EconomicCalendar: failed to fetch events", exc_info=True)
            return []

        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours_ahead)
        result: list[dict] = []

        for event in events:
            if not self._is_high_impact(event):
                continue
            if currencies:
                event_currency = str(event.get("currency", "")).upper()
                if event_currency not in [c.upper() for c in currencies]:
                    continue
            event_time = self._parse_event_time(event)
            if event_time is None:
                continue
            if now <= event_time <= cutoff:
                result.append(event)

        return result

    # ── Internal helpers ───────────────────────────────────────────────

    def _fetch_from_finnhub(self) -> list[dict]:
        """Call the Finnhub economic calendar endpoint."""
        if not self.finnhub_key:
            logger.debug("EconomicCalendar: no Finnhub key configured – returning empty")
            return []

        now = datetime.now(timezone.utc)
        from_date = now.strftime("%Y-%m-%d")
        to_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")

        params: dict[str, Any] = {
            "token": self.finnhub_key,
            "from": from_date,
            "to": to_date,
        }

        try:
            resp = requests.get(
                _FINNHUB_CALENDAR_URL,
                params=params,
                timeout=(10, 20),
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            logger.warning("EconomicCalendar: HTTP error fetching Finnhub events: %s", exc)
            return []
        except ValueError as exc:
            logger.warning("EconomicCalendar: JSON decode error: %s", exc)
            return []

        # Finnhub returns {"economicCalendar": [...]} or just a list
        if isinstance(payload, dict):
            raw_events = payload.get("economicCalendar", payload.get("result", []))
        elif isinstance(payload, list):
            raw_events = payload
        else:
            logger.warning("EconomicCalendar: unexpected response shape: %r", type(payload))
            return []

        if not isinstance(raw_events, list):
            logger.warning("EconomicCalendar: events field is not a list")
            return []

        events = [self._normalise_event(e) for e in raw_events if isinstance(e, dict)]
        logger.info("EconomicCalendar: fetched %d events from Finnhub", len(events))
        return events

    @staticmethod
    def _normalise_event(raw: dict) -> dict:
        """Normalise a Finnhub event dict to a consistent schema."""
        # Finnhub uses 'time' (epoch seconds) or 'date' (ISO string) fields
        dt_str = ""
        if raw.get("time"):
            try:
                ts = float(raw["time"])
                dt_str = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except (ValueError, TypeError, OSError):
                dt_str = str(raw["time"])
        elif raw.get("date"):
            dt_str = str(raw["date"])

        impact_raw = str(raw.get("impact", raw.get("importance", ""))).lower()
        # Finnhub uses "high" / "medium" / "low" or numeric strings
        if impact_raw in ("3", "high"):
            impact = "high"
        elif impact_raw in ("2", "medium"):
            impact = "medium"
        elif impact_raw in ("1", "low"):
            impact = "low"
        else:
            impact = impact_raw or ""

        return {
            "datetime": dt_str,
            "event": str(raw.get("event", raw.get("name", ""))),
            "impact": impact,
            "currency": str(raw.get("currency", raw.get("country", ""))).upper(),
            "actual": raw.get("actual"),
            "estimate": raw.get("estimate"),
            "prev": raw.get("prev"),
        }

    @staticmethod
    def _is_high_impact(event: dict) -> bool:
        return str(event.get("impact", "")).lower() in ("high", "3")

    @staticmethod
    def _parse_event_time(event: dict) -> datetime | None:
        dt_str = event.get("datetime", "")
        if not dt_str:
            return None
        try:
            dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            pass
        # Try epoch seconds
        try:
            ts = float(dt_str)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, TypeError):
            return None
