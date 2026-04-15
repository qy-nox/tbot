"""
Pydantic schemas for API request / response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from signal_platform.models import (
    DeliveryChannel,
    DeliveryStatus,
    SignalDirection,
    SignalGrade,
    SignalOutcome,
    SignalType,
    SubscriptionTier,
)


# ── Auth ────────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    telegram_chat_id: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User ────────────────────────────────────────────────────────────────


class UserProfile(BaseModel):
    id: int
    username: str
    email: str
    subscription_tier: SubscriptionTier
    is_active: bool
    telegram_chat_id: Optional[str] = None
    discord_user_id: Optional[str] = None
    timezone: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    telegram_chat_id: Optional[str] = None
    discord_user_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


# ── Signals ─────────────────────────────────────────────────────────────


class SignalCreate(BaseModel):
    """Admin / bot endpoint to create a new signal."""
    signal_type: SignalType = SignalType.CRYPTO
    pair: str
    direction: SignalDirection
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    confidence: float = Field(..., ge=0, le=1)
    strategy: Optional[str] = None
    reason: Optional[str] = None
    valid_minutes: int = 60
    # binary-specific
    binary_duration: Optional[int] = None
    binary_direction: Optional[str] = None


class SignalResponse(BaseModel):
    id: int
    timestamp: datetime
    signal_type: SignalType
    pair: str
    direction: SignalDirection
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    confidence: float
    grade: Optional[SignalGrade] = None
    strategy: Optional[str] = None
    reason: Optional[str] = None
    valid_until: Optional[datetime] = None
    risk_reward_ratio: Optional[float] = None
    outcome: SignalOutcome
    pnl_percent: Optional[float] = None
    binary_duration: Optional[int] = None
    binary_direction: Optional[str] = None

    model_config = {"from_attributes": True}


class SignalResultUpdate(BaseModel):
    """Update signal outcome after market resolution."""
    outcome: SignalOutcome
    actual_exit_price: Optional[float] = None
    pnl_percent: Optional[float] = None


# ── Performance ─────────────────────────────────────────────────────────


class PerformanceOverview(BaseModel):
    total_signals: int
    winning: int
    losing: int
    pending: int
    win_rate: float
    total_pnl_percent: float
    avg_pnl_percent: float
    best_signal_pnl: Optional[float] = None
    worst_signal_pnl: Optional[float] = None


class PairPerformance(BaseModel):
    pair: str
    total_signals: int
    win_rate: float
    avg_pnl_percent: float


class LeaderboardEntry(BaseModel):
    pair: str
    win_rate: float
    total_signals: int
    total_pnl_percent: float


# ── Subscription ────────────────────────────────────────────────────────


class SubscriptionPlanResponse(BaseModel):
    id: int
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    max_signals_per_day: int
    features: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class CreatePaymentRequest(BaseModel):
    tier: SubscriptionTier
    provider: str = "stripe"  # stripe / paypal / crypto
    period: str = "monthly"   # monthly / yearly


class PaymentResponse(BaseModel):
    id: int
    amount: float
    currency: str
    provider: str
    status: str
    subscription_tier: Optional[SubscriptionTier] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Delivery ────────────────────────────────────────────────────────────


class DeliveryStatusResponse(BaseModel):
    id: int
    signal_id: int
    channel: DeliveryChannel
    status: DeliveryStatus
    retry_count: int
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Admin ───────────────────────────────────────────────────────────────


class AdminDashboard(BaseModel):
    total_users: int
    active_users: int
    premium_users: int
    vip_users: int
    total_signals_today: int
    total_revenue: float
    win_rate_7d: float
    pending_signals: int


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    subscription_tier: Optional[SubscriptionTier] = None
