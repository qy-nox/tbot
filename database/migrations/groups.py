"""Migration for signal_groups extension table."""

from __future__ import annotations

from sqlalchemy import text

from signal_platform.models import get_engine

SQL = """
CREATE TABLE IF NOT EXISTS signal_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    link VARCHAR(255) NOT NULL,
    signal_filter VARCHAR(50) DEFAULT 'all',
    is_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP
);
"""


def run() -> str:
    with get_engine().begin() as connection:
        connection.execute(text(SQL))
    return "signal_groups_migrated"
