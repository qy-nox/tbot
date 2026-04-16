"""Email service with HTML template support."""

from __future__ import annotations


def render_signal_email(title: str, message: str) -> str:
    return f"<html><body><h2>{title}</h2><p>{message}</p></body></html>"
