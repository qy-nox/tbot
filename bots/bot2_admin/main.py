"""CLI entrypoint for Bot 2 (admin control)."""

from __future__ import annotations

import argparse

from bots.bot2_admin.handlers import handle_list_users
from signal_platform.models import get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot2 Admin helper")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    db = get_session()
    try:
        print(handle_list_users(db, limit=args.limit))
    finally:
        db.close()


if __name__ == "__main__":
    main()
