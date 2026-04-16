"""Webhook management for custom integrations."""

from __future__ import annotations

import requests


def post_webhook(url: str, payload: dict) -> bool:
    if not url:
        return False
    try:
        response = requests.post(url, json=payload, timeout=10)
    except requests.RequestException:
        return False
    return response.status_code < 300
