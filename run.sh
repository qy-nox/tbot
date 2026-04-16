#!/usr/bin/env bash
set -euo pipefail

command -v python >/dev/null 2>&1 || { echo "python is required but not found"; exit 1; }
[[ -f main.py ]] || { echo "main.py not found in current directory"; exit 1; }

python main.py --both
