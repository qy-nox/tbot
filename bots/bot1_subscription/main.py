"""CLI entrypoint for Bot 1 (subscription flow)."""

from __future__ import annotations

import argparse

from bots.bot1_subscription.database import open_session
from bots.bot1_subscription.handlers import handle_subscribe


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot1 Subscription helper")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--tier", choices=["free", "premium", "vip"], default="premium")
    args = parser.parse_args()

    db = open_session()
    try:
        print(handle_subscribe(db, user_id=args.user_id, tier=args.tier))
    finally:
        db.close()


if __name__ == "__main__":
    main()
