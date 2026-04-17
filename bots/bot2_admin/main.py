"""Deprecated compatibility entrypoint for removed admin Telegram bot."""


def main() -> None:
    raise RuntimeError("Admin Telegram bot was removed. Use the admin website at /admin/.")


if __name__ == "__main__":
    main()
