"""Base exchange trader class."""

from __future__ import annotations


class BaseTrader:
    name = "base"

    def place_order(self, symbol: str, side: str, amount: float) -> dict:
        return {"exchange": self.name, "symbol": symbol, "side": side, "amount": amount, "status": "simulated"}
