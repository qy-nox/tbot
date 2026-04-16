"""Schema migration helpers and extension migration entrypoints."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from signal_platform.models import get_engine


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    escaped = False

    for char in sql:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            continue

        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double

        if char == ";" and not in_single and not in_double:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def run_migrations() -> str:
    """Apply base schema.sql to the configured database."""
    schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql)

    with get_engine().begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

    return f"migrations_applied:{len(statements)}"
