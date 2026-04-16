"""Compatibility database module for signal platform."""

from signal_platform.models import Base, get_engine, get_session, init_db

__all__ = ["Base", "get_engine", "get_session", "init_db"]
