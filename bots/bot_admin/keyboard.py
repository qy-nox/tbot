"""Keyboard layouts for admin bot."""

from __future__ import annotations


def admin_panel_keyboard() -> list[dict[str, str]]:
    return [
        {"text": "💳 Payments", "callback_data": "admin:payments"},
        {"text": "👥 Users", "callback_data": "admin:users"},
        {"text": "📡 Groups", "callback_data": "admin:groups"},
        {"text": "📊 Stats", "callback_data": "admin:stats"},
    ]
