"""CLI entrypoint for subscription bot commands."""

from __future__ import annotations

import argparse

from bots.bot_subscription.handlers import (
    handle_billing,
    handle_plans,
    handle_start,
    handle_status,
    handle_subscribe,
    handle_transaction,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscription Bot helper")
    parser.add_argument("--command", choices=["start", "plans", "subscribe", "status", "billing", "transaction"], default="start")
    parser.add_argument("--username", default="demo_user")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--telegram-id", default="1001")
    parser.add_argument("--plan", choices=["free", "premium", "vip"], default="free")
    parser.add_argument("--tx", default="")
    args = parser.parse_args()

    if args.command == "start":
        print(handle_start())
    elif args.command == "plans":
        print(handle_plans())
    elif args.command == "subscribe":
        print(handle_subscribe(username=args.username, user_id=args.user_id, telegram_id=args.telegram_id, plan=args.plan))
    elif args.command == "transaction":
        print(handle_transaction(user_id=args.user_id, transaction_id=args.tx or "demo-tx"))
    elif args.command == "status":
        print(handle_status(args.user_id))
    else:
        print(handle_billing(args.user_id))


if __name__ == "__main__":
    main()
