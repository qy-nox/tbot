"""Admin analytics for dashboard summaries."""

from __future__ import annotations

from database.models import Signal, User


def dashboard_stats(db) -> dict[str, object]:
    """Return reusable dashboard statistics payload."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    total_signals = db.query(Signal).count()
    pending_signals = db.query(Signal).filter(Signal.status == "pending").count()
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_signals": total_signals,
        "pending_signals": pending_signals,
    }
