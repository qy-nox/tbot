"""Database access helpers for subscription bot."""

from signal_platform.models import get_session


def open_session():
    return get_session()
