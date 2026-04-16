"""Database access helpers for admin control bot."""

from signal_platform.models import get_session


def open_session():
    """Open a shared SQLAlchemy session for admin operations."""
    return get_session()
