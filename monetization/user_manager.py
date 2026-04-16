"""Monetization-facing user manager."""

from __future__ import annotations

from signal_platform.services.user_service import UserService


class UserManager:
    service = UserService
