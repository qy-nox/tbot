"""Admin management operations for users/payments/signals."""

from __future__ import annotations

from database.models import Signal, User


def list_users(db, limit: int = 20) -> list[User]:
    return db.query(User).order_by(User.id.desc()).limit(limit).all()


def list_signals(db, limit: int = 20) -> list[Signal]:
    return db.query(Signal).order_by(Signal.id.desc()).limit(limit).all()
