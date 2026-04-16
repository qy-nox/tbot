"""Discord delivery integration."""

from __future__ import annotations

import requests


def send_discord(webhook_url: str, content: str) -> bool:
    if not webhook_url:
        return False
    response = requests.post(webhook_url, json={"content": content}, timeout=10)
    return response.status_code < 300
