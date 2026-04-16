"""Compatibility entrypoint for the subscription Telegram bot."""

from bots.bot_subscription import main as subscription_main


def main() -> None:
    subscription_main.main()


if __name__ == "__main__":
    main()
