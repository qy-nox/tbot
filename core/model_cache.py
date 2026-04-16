"""Model caching utilities for advanced ML components."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from config.settings import BASE_DIR


class ModelCache:
    """Simple filesystem-backed model cache."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or (BASE_DIR / "model_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name: str) -> Any | None:
        path = self.cache_dir / f"{name}.pkl"
        if not path.exists():
            return None
        return joblib.load(path)

    def save(self, name: str, model: Any) -> Path:
        path = self.cache_dir / f"{name}.pkl"
        joblib.dump(model, path)
        return path
