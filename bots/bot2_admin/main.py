"""Compatibility entrypoint for the admin Telegram bot."""

from bots.bot_admin import main as admin_main


def main() -> None:
    admin_main.main()


if __name__ == "__main__":
    main()
