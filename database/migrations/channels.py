"""Migration for channel_configs extension table."""

from __future__ import annotations

from sqlalchemy import text

from signal_platform.models import get_engine

SQL = """
CREATE TABLE IF NOT EXISTS channel_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    subscribers INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT 1,
    revenue_share FLOAT DEFAULT 0,
    created_at TIMESTAMP
);
"""


def run() -> str:
    with get_engine().begin() as connection:
        connection.execute(text(SQL))
    return "channel_configs_migrated"
