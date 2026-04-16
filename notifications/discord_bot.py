"""Discord delivery integration."""

from __future__ import annotations

import requests


def send_discord(webhook_url: str, content: str) -> bool:
    if not webhook_url:
        return False
    try:
        response = requests.post(webhook_url, json={"content": content}, timeout=10)
    except requests.RequestException:
        return False
    return response.status_code < 300
