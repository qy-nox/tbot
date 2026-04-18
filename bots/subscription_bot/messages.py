"""Formatted user-facing messages for the subscription bot."""

from __future__ import annotations


def welcome_message() -> str:
    return "👋 Welcome! Choose a subscription plan to access graded trading signals."


def payment_prompt(plan: str) -> str:
    return f"💳 You selected {plan.upper()}. Choose Binance P2P, bKash, or Manual Bank Transfer."


def status_message(status: str) -> str:
    return f"📌 Subscription status: {status}."
