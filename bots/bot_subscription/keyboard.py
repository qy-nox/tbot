"""Keyboard layouts for subscription bot."""

from __future__ import annotations


def continue_keyboard() -> list[dict[str, str]]:
    return [{"text": "Continue", "callback_data": "subscription:continue"}]


def plans_keyboard() -> list[dict[str, str]]:
    return [
        {"text": "🆓 Free ($0)", "callback_data": "plan:free"},
        {"text": "⭐ Premium ($29.99/month)", "callback_data": "plan:premium"},
        {"text": "👑 VIP ($79.99/month)", "callback_data": "plan:vip"},
    ]


def payment_options_keyboard() -> list[dict[str, str]]:
    return [
        {"text": "USDT", "callback_data": "pay:usdt"},
        {"text": "Stripe", "callback_data": "pay:stripe"},
        {"text": "Bank Transfer", "callback_data": "pay:bank"},
    ]
