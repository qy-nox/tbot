"""Parameter optimization helpers."""

from __future__ import annotations

from typing import Callable


def grid_search(params: dict[str, list], scorer: Callable[[dict], float]) -> tuple[dict, float]:
    if not params or any(len(values) == 0 for values in params.values()):
        return {}, 0.0

    best_params: dict = {}
    best_score = float("-inf")
    keys = list(params.keys())

    def _walk(index: int, current: dict) -> None:
        nonlocal best_params, best_score
        if index >= len(keys):
            score = scorer(current)
            if score > best_score:
                best_params = dict(current)
                best_score = score
            return
        key = keys[index]
        for value in params[key]:
            current[key] = value
            _walk(index + 1, current)

    _walk(0, {})
    return best_params, best_score
