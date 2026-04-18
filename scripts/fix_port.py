"""Release a busy API port used by local tbot services."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import time


def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _port_owner_pids(port: int) -> list[int]:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return []
    pids: list[int] = []
    for raw in result.stdout.splitlines():
        value = raw.strip()
        if value.isdigit():
            pids.append(int(value))
    return [pid for pid in pids if pid != os.getpid()]


def _pid_command(pid: int) -> str:
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""
    return result.stdout.strip()


def _belongs_to_tbot(pid: int) -> bool:
    cmd = _pid_command(pid).lower()
    return "tbot" in cmd or "main.py --both" in cmd or "main.py --api" in cmd


def release_port(host: str, port: int, wait_seconds: float = 5.0, force: bool = False) -> bool:
    if _is_port_available(host, port):
        return True
    pids = _port_owner_pids(port)
    if not pids:
        return False

    for pid in pids:
        if not force and not _belongs_to_tbot(pid):
            print(f"skip pid={pid} (not recognized as tbot): {_pid_command(pid)}")
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"sent SIGTERM to pid={pid}")
        except ProcessLookupError:
            pass
        except PermissionError:
            print(f"permission denied for pid={pid}")

    deadline = time.time() + max(0.5, wait_seconds)
    while time.time() < deadline:
        if _is_port_available(host, port):
            return True
        time.sleep(0.2)
    return _is_port_available(host, port)


def main() -> int:
    parser = argparse.ArgumentParser(description="Release a busy API port.")
    parser.add_argument("--host", default=os.getenv("API_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("API_PORT", "8000")))
    parser.add_argument("--wait", type=float, default=5.0)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow killing non-tbot processes on the target port.",
    )
    args = parser.parse_args()

    if release_port(args.host, args.port, wait_seconds=args.wait, force=args.force):
        print(f"OK: {args.host}:{args.port} is available.")
        return 0
    print(
        f"ERROR: Could not free {args.host}:{args.port}. "
        "Use a different API_PORT or stop the owning process manually."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
