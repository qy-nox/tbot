"""User management service wrapper."""

from __future__ import annotations

from database.models import User
from database.queries import get_user_by_telegram_id


def get_or_create_user(db, *, telegram_id: str, username: str | None = None) -> User:
    user = get_user_by_telegram_id(db, telegram_id)
    if user is not None:
        return user
    user = User(telegram_id=telegram_id, username=username, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
