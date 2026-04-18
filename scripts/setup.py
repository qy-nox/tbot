"""Interactive setup helper for the Telegram ecosystem."""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    env_path = Path('.env')
    if not env_path.exists():
        try:
            template = Path('.env.example').read_text(encoding='utf-8')
        except OSError as exc:
            raise RuntimeError('Failed to copy .env.example: file not found or unreadable') from exc
        env_path.write_text(template, encoding='utf-8')
    print('Setup complete. Review .env and run: python scripts/init_db.py')


if __name__ == '__main__':
    main()
