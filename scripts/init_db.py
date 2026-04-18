"""Initialize ecosystem database tables."""

from __future__ import annotations

from database.queries import init_schema


def main() -> None:
    init_schema()


if __name__ == "__main__":
    main()
