"""CLI entrypoint for admin bot commands."""

from __future__ import annotations

import argparse

from bots.bot_admin.handlers import (
    handle_admin,
    handle_ban,
    handle_groups,
    handle_payments,
    handle_stats,
    handle_unban,
    handle_users,
)
from signal_platform.models import get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Admin Bot helper")
    parser.add_argument("--command", choices=["admin", "payments", "users", "groups", "stats", "ban", "unban"], default="admin")
    parser.add_argument("--user-id", type=int, default=1)
    args = parser.parse_args()

    if args.command in {"admin", "groups"}:
        print(handle_admin() if args.command == "admin" else handle_groups())
        return

    db = get_session()
    try:
        if args.command == "payments":
            print(handle_payments(db))
        elif args.command == "users":
            print(handle_users(db))
        elif args.command == "stats":
            print(handle_stats(db))
        elif args.command == "ban":
            print(handle_ban(db, args.user_id))
        else:
            print(handle_unban(db, args.user_id))
    finally:
        db.close()


if __name__ == "__main__":
    main()
