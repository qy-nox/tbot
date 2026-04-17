"""Simple, dependency-light news aggregation primitives."""

from __future__ import annotations

from dataclasses import dataclass
import ssl
from datetime import datetime
from typing import Callable, Iterable
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen
from xml.etree import ElementTree


@dataclass
class NewsItem:
    source: str
    title: str
    url: str = ""
    published_at: datetime | None = None


class NewsAggregator:
    def __init__(
        self,
        timeout_seconds: float = 5.0,
        max_items: int = 25,
        allow_http: bool = False,
        max_xml_size_bytes: int = 2_000_000,
    ):
        self.timeout_seconds = timeout_seconds
        self.max_items = max_items
        self.allow_http = allow_http
        self.max_xml_size_bytes = max(1, int(max_xml_size_bytes))

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
            key = (item.title.strip().lower(), self._normalize_url(item.url))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        return deduped[: self.max_items]

    def fetch_rss(self, source: str, rss_url: str) -> list[NewsItem]:
        parsed = urlparse(rss_url)
        allowed_schemes = {"https", "http"} if self.allow_http else {"https"}
        if parsed.scheme.lower() not in allowed_schemes:
            return []
        try:
            ssl_context = ssl.create_default_context()
            with urlopen(rss_url, timeout=self.timeout_seconds, context=ssl_context) as response:
                content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                allowed_content_types = {"application/xml", "text/xml", "application/rss+xml", "application/atom+xml"}
                if content_type not in allowed_content_types:
                    return []
                xml_content = response.read()
            if len(xml_content) > self.max_xml_size_bytes:
                return []
            lowered = xml_content.lower()
            if b"<!doctype" in lowered or b"<!entity" in lowered:
                return []
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

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse((url or "").strip().lower())
        if not parsed.scheme and not parsed.netloc:
            return ""
        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                "",
                "",
            )
        )
