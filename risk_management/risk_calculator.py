"""Risk metric calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class RiskPlan:
    position_size: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    account_heat: float


class RiskCalculator:
    def __init__(self, daily_loss_limit_pct: float = 5.0, max_open_positions: int = 5) -> None:
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_open_positions = max_open_positions

    @staticmethod
    def position_size(account_balance: float, risk_pct: float, entry: float, stop_loss: float, correlation_factor: float = 1.0) -> float:
        risk_amount = account_balance * max(risk_pct, 0) * max(min(correlation_factor, 1.0), 0.1)
        stop_distance = abs(entry - stop_loss)
        if stop_distance <= 0:
            return 0.0
        return risk_amount / stop_distance

    @staticmethod
    def atr_stop_loss(entry: float, atr: float, direction: str, multiplier: float = 1.5) -> float:
        distance = atr * multiplier
        if direction.upper() == "BUY":
            return entry - distance
        return entry + distance

    @staticmethod
    def fixed_stop_loss(entry: float, direction: str, stop_pct: float) -> float:
        distance = entry * stop_pct
        if direction.upper() == "BUY":
            return entry - distance
        return entry + distance

    @staticmethod
    def trailing_stop(current_price: float, atr: float, direction: str, multiplier: float = 1.0) -> float:
        distance = atr * multiplier
        if direction.upper() == "BUY":
            return current_price - distance
        return current_price + distance

    @staticmethod
    def take_profit_levels(entry: float, stop_loss: float, direction: str) -> tuple[float, float, float]:
        risk = abs(entry - stop_loss)
        if direction.upper() == "BUY":
            return (entry + risk * 2.0, entry + risk * 2.5, entry + risk * 3.0)
        return (entry - risk * 2.0, entry - risk * 2.5, entry - risk * 3.0)

    @staticmethod
    def risk_reward(entry: float, stop_loss: float, take_profit: float) -> float:
        risk = abs(entry - stop_loss)
        if risk == 0:
            return 0.0
        return abs(take_profit - entry) / risk

    @staticmethod
    def account_heat(open_risk_amounts: list[float], account_balance: float) -> float:
        if account_balance <= 0:
            return 0.0
        return sum(open_risk_amounts) / account_balance

    def is_daily_loss_limit_hit(self, daily_pnl: float, account_balance: float) -> bool:
        if account_balance <= 0:
            return False
        loss_pct = abs(min(daily_pnl, 0.0)) / account_balance * 100
        return loss_pct >= self.daily_loss_limit_pct

    def can_open_new_position(self, open_positions: int) -> bool:
        return open_positions < self.max_open_positions

    def build_plan(
        self,
        *,
        account_balance: float,
        risk_pct: float,
        entry: float,
        direction: str,
        atr: float,
        open_risk_amounts: list[float] | None = None,
    ) -> RiskPlan:
        stop_loss = self.atr_stop_loss(entry, atr, direction)
        size = self.position_size(account_balance, risk_pct, entry, stop_loss)
        tp1, tp2, tp3 = self.take_profit_levels(entry, stop_loss, direction)
        heat = self.account_heat(open_risk_amounts or [], account_balance)
        return RiskPlan(
            position_size=round(size, 8),
            stop_loss=round(stop_loss, 8),
            take_profit_1=round(tp1, 8),
            take_profit_2=round(tp2, 8),
            take_profit_3=round(tp3, 8),
            account_heat=round(heat, 8),
        )


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    if avg_loss <= 0:
        return 0.0
    b = avg_win / avg_loss
    return max(0.0, (win_rate * b - (1 - win_rate)) / b)


def sharpe_ratio(returns: list[float]) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    return 0.0 if std == 0 else mean / std
