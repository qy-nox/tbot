"""Admin command helpers."""

from signal_platform.services.user_service import UserService


def list_users(db, *, limit: int = 20):
    return UserService.list_users(db, limit=limit)
