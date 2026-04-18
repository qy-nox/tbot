"""Start API plus all three Telegram bot entrypoints."""

from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [sys.executable, "main.py", "--both"],
    [sys.executable, "-m", "bots.main_signal_bot.main"],
    [sys.executable, "-m", "bots.subscription_bot.main"],
    [sys.executable, "-m", "bots.admin_bot.main"],
]


def main() -> None:
    processes: list[subprocess.Popen] = []
    try:
        for cmd in COMMANDS:
            processes.append(subprocess.Popen(cmd))
        for process in processes:
            process.wait()
            if process.returncode not in (0, None):
                raise RuntimeError(f"Process exited with code {process.returncode}")
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
    except OSError as exc:
        for process in processes:
            process.terminate()
        raise RuntimeError("Failed to start one or more services") from exc


if __name__ == "__main__":
    main()
