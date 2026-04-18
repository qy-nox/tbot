"""Cleanup logs, caches, and temporary runtime files."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REMOVE_DIRS = [
    ROOT / ".pytest_cache",
    ROOT / "__pycache__",
    ROOT / "logs" / "__pycache__",
]
REMOVE_GLOBS = [
    "logs/*.log",
    "**/__pycache__",
    "**/*.pyc",
]


def main() -> int:
    removed = 0
    for directory in REMOVE_DIRS:
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)
            print(f"removed directory: {directory}")
            removed += 1

    for pattern in REMOVE_GLOBS:
        for path in ROOT.glob(pattern):
            if not path.exists():
                continue
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
            print(f"removed: {path}")
            removed += 1

    print(f"cleanup complete; removed {removed} item(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
