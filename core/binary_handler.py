"""Binary options broker credential and signal helper."""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import Settings
from trading.binary_trader import BinaryTrader


@dataclass(frozen=True)
class BinaryCredentials:
    iq_option_email: str
    iq_option_password: str
    pocket_option_token: str


class BinaryHandler:
    """Small façade that centralizes binary credentials and signal generation."""

    def __init__(self) -> None:
        self.credentials = BinaryCredentials(
            iq_option_email=Settings.IQ_OPTION_EMAIL,
            iq_option_password=Settings.IQ_OPTION_PASSWORD,
            pocket_option_token=Settings.POCKET_OPTION_TOKEN,
        )
        self._trader = BinaryTrader()

    def configured(self) -> bool:
        return bool(
            (self.credentials.iq_option_email and self.credentials.iq_option_password)
            or self.credentials.pocket_option_token
        )

    def generate_signal(self, **kwargs) -> dict | None:
        """Proxy signal generation to :class:`trading.binary_trader.BinaryTrader`.

        Expected keyword arguments mirror ``BinaryTrader.generate_signal``:
        pair, timeframe, rsi, ema20, ema50, close, bb_upper, bb_lower.
        """
        return self._trader.generate_signal(**kwargs)
