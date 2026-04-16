"""User administration helpers for admin bot."""

from __future__ import annotations

from signal_platform.services.user_service import UserService


def list_users(db, *, limit: int = 50):
    return UserService.list_users(db, limit=limit)


def ban_user(db, user_id: int):
    return UserService.admin_update(db, user_id, is_active=False)


def unban_user(db, user_id: int):
    return UserService.admin_update(db, user_id, is_active=True)
