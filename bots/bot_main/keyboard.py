"""Keyboard layouts for the main signal bot."""

from __future__ import annotations


def main_menu_keyboard() -> list[dict[str, str]]:
    return [
        {"text": "📈 Market", "callback_data": "main:market"},
        {"text": "🎯 Signals", "callback_data": "main:signals"},
        {"text": "📊 Performance", "callback_data": "main:performance"},
        {"text": "❓ Help", "callback_data": "main:help"},
    ]


def signal_actions_keyboard() -> list[dict[str, str]]:
    return [
        {"text": "🔄 Refresh", "callback_data": "main:refresh"},
        {"text": "ℹ️ Details", "callback_data": "main:details"},
    ]
