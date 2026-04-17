"""Simple, dependency-light news aggregation primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable
from urllib.request import urlopen
from xml.etree import ElementTree


@dataclass
class NewsItem:
    source: str
    title: str
    url: str = ""
    published_at: datetime | None = None


class NewsAggregator:
    def __init__(self, timeout_seconds: float = 5.0, max_items: int = 25):
        self.timeout_seconds = timeout_seconds
        self.max_items = max_items

    def aggregate(self, providers: dict[str, Callable[[], Iterable[dict | NewsItem]]] | None = None) -> list[NewsItem]:
        providers = providers or {}
        merged: list[NewsItem] = []
        for source, provider in providers.items():
            try:
                for item in provider() or []:
                    normalized = self._normalize(item, default_source=source)
                    if normalized.title:
                        merged.append(normalized)
            except Exception:
                continue

        deduped: list[NewsItem] = []
        seen: set[tuple[str, str]] = set()
        for item in merged:
            key = (item.title.strip().lower(), item.url.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        return deduped[: self.max_items]

    def fetch_rss(self, source: str, rss_url: str) -> list[NewsItem]:
        try:
            with urlopen(rss_url, timeout=self.timeout_seconds) as response:
                xml_content = response.read()
            root = ElementTree.fromstring(xml_content)
            results: list[NewsItem] = []
            for node in root.findall(".//item"):
                title = (node.findtext("title") or "").strip()
                link = (node.findtext("link") or "").strip()
                if title:
                    results.append(NewsItem(source=source, title=title, url=link))
            return results[: self.max_items]
        except Exception:
            return []

    @staticmethod
    def _normalize(item: dict | NewsItem, default_source: str) -> NewsItem:
        if isinstance(item, NewsItem):
            return item

        return NewsItem(
            source=str(item.get("source") or default_source),
            title=str(item.get("title") or item.get("headline") or ""),
            url=str(item.get("url") or item.get("link") or ""),
            published_at=item.get("published_at") if isinstance(item.get("published_at"), datetime) else None,
        )
