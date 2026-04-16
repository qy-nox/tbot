"""Simple schema migration helpers for the database package."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from signal_platform.models import get_engine


def run_migrations() -> str:
    """Apply the SQL schema file to the configured database."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    engine = get_engine()
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
    return "migrations_applied"
