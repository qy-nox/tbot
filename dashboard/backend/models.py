"""Pydantic models used by the dashboard backend API."""

from __future__ import annotations

from pydantic import BaseModel


class DashboardUser(BaseModel):
    id: int
    username: str
    tier: str
    is_active: bool


class DashboardSubscription(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    tier: str | None


class DashboardSignal(BaseModel):
    id: int
    pair: str
    direction: str
    grade: str | None
    confidence: float | None


class MarketAsset(BaseModel):
    symbol: str
    price: float
    change_24h: float


class DashboardStats(BaseModel):
    total_users: int
    total_revenue: float
    win_rate: float
