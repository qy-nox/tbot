"""Emergency recovery: stop stale tbot processes, clean, and restart."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _list_tbot_pids() -> list[int]:
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,command="],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pid_text, command = line.split(maxsplit=1)
        except ValueError:
            continue
        if not pid_text.isdigit():
            continue
        pid = int(pid_text)
        if pid == os.getpid():
            continue
        lowered = command.lower()
        if "tbot" in lowered and "python" in lowered:
            pids.append(pid)
    return pids


def _stop_tbot_processes() -> None:
    for pid in _list_tbot_pids():
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"sent SIGTERM to pid={pid}")
        except ProcessLookupError:
            pass
        except PermissionError:
            print(f"permission denied for pid={pid}")
    time.sleep(1.0)


def _run(script: str) -> None:
    path = ROOT / "scripts" / script
    subprocess.run([sys.executable, str(path)], check=False)


def main() -> int:
    print("=== EMERGENCY RESTART ===")
    _stop_tbot_processes()
    _run("fix_port.py")
    _run("cleanup.py")
    print("starting services...")
    subprocess.Popen([sys.executable, str(ROOT / "run.py")], cwd=ROOT, start_new_session=True)
    print("done. verify with: python scripts/health_check.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
