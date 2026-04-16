"""Parameter optimization helpers."""

from __future__ import annotations

from typing import Callable


def grid_search(params: dict[str, list], scorer: Callable[[dict], float]) -> tuple[dict, float]:
    best_params: dict = {}
    best_score = float("-inf")

    def _walk(keys: list[str], current: dict) -> None:
        nonlocal best_params, best_score
        if not keys:
            score = scorer(current)
            if score > best_score:
                best_params = dict(current)
                best_score = score
            return
        key = keys[0]
        for value in params.get(key, []):
            current[key] = value
            _walk(keys[1:], current)

    _walk(list(params.keys()), {})
    return best_params, best_score
