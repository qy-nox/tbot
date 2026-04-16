"""Migration for subscription_records extension table."""

from __future__ import annotations

from sqlalchemy import text

from signal_platform.models import get_engine

SQL = """
CREATE TABLE IF NOT EXISTS subscription_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    payment_date TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
"""


def run() -> str:
    with get_engine().begin() as connection:
        connection.execute(text(SQL))
    return "subscription_records_migrated"
