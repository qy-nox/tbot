"""
Extended database models for the Professional Trading Signal Service Platform.

Tables
------
- User              – authentication, profile, subscription tier
- Subscription      – plan metadata (Free / Premium / VIP)
- Payment           – billing history & invoices
- SignalRecord       – every signal with quality metadata
- SignalResult      – outcome tracking (hit TP / hit SL / expired)
- SignalDelivery    – per-user delivery status
- PerformanceSnapshot – periodic win-rate / ROI snapshots
- AuditLog          – security & compliance trail
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from config.settings import Settings


# ── Helpers ─────────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ───────────────────────────────────────────────────────────────


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    VIP = "vip"


class SignalGrade(str, enum.Enum):
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"


class SignalDirection(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class SignalType(str, enum.Enum):
    CRYPTO = "crypto"
    BINARY = "binary"


class SignalOutcome(str, enum.Enum):
    PENDING = "pending"
    TP1_HIT = "tp1_hit"
    TP2_HIT = "tp2_hit"
    TP3_HIT = "tp3_hit"
    SL_HIT = "sl_hit"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class DeliveryChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    API = "api"


# ── Base ────────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ── User ────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    subscription_tier = Column(
        Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False
    )
    telegram_chat_id = Column(String(50))
    discord_user_id = Column(String(50))
    whatsapp_number = Column(String(20))
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    last_login = Column(DateTime)

    # relationships
    payments = relationship("Payment", back_populates="user", lazy="dynamic")
    deliveries = relationship("SignalDelivery", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User {self.username} tier={self.subscription_tier.value}>"


# ── Subscription Plan ───────────────────────────────────────────────────


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tier = Column(Enum(SubscriptionTier), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    price_monthly = Column(Float, default=0.0)
    price_yearly = Column(Float, default=0.0)
    max_signals_per_day = Column(Integer, default=5)
    features = Column(Text)  # JSON list of feature strings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


# ── Payment ─────────────────────────────────────────────────────────────


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    provider = Column(String(20))  # stripe / paypal / crypto
    provider_tx_id = Column(String(120))
    status = Column(String(20), default="pending")  # pending / completed / failed / refunded
    subscription_tier = Column(Enum(SubscriptionTier))
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="payments")


# ── Signal Record ───────────────────────────────────────────────────────


class SignalRecord(Base):
    """Every signal produced by the bot with full metadata."""

    __tablename__ = "signal_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    signal_type = Column(Enum(SignalType), default=SignalType.CRYPTO, nullable=False)
    pair = Column(String(20), nullable=False, index=True)
    direction = Column(Enum(SignalDirection), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    take_profit_3 = Column(Float)
    confidence = Column(Float)
    grade = Column(Enum(SignalGrade))
    strategy = Column(String(50))
    reason = Column(Text)
    valid_until = Column(DateTime)  # signal expiry
    risk_reward_ratio = Column(Float)
    # Binary-specific fields
    binary_duration = Column(Integer)  # seconds for binary options
    binary_direction = Column(String(10))  # CALL / PUT

    # outcome tracking
    outcome = Column(Enum(SignalOutcome), default=SignalOutcome.PENDING)
    actual_exit_price = Column(Float)
    pnl_percent = Column(Float)
    closed_at = Column(DateTime)

    # relationships
    deliveries = relationship("SignalDelivery", back_populates="signal", lazy="dynamic")

    def __repr__(self) -> str:
        return (
            f"<SignalRecord {self.pair} {self.direction.value} "
            f"grade={self.grade} conf={self.confidence:.0%}>"
        )


# ── Signal Delivery ─────────────────────────────────────────────────────


class SignalDelivery(Base):
    """Tracks delivery of each signal to each user/channel."""

    __tablename__ = "signal_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey("signal_records.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    channel = Column(Enum(DeliveryChannel), nullable=False)
    channel_target = Column(String(120))  # chat_id / webhook URL / email
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=_utcnow)

    signal = relationship("SignalRecord", back_populates="deliveries")
    user = relationship("User", back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("signal_id", "user_id", "channel", name="uq_delivery"),
    )


# ── Performance Snapshot ────────────────────────────────────────────────


class PerformanceSnapshot(Base):
    """Periodic (daily / weekly / monthly) performance aggregation."""

    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), nullable=False)  # daily / weekly / monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    pair = Column(String(20))  # NULL = all pairs
    total_signals = Column(Integer, default=0)
    winning_signals = Column(Integer, default=0)
    losing_signals = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    avg_pnl_percent = Column(Float, default=0.0)
    best_signal_pnl = Column(Float)
    worst_signal_pnl = Column(Float)
    avg_confidence = Column(Float)
    created_at = Column(DateTime, default=_utcnow)


# ── Audit Log ───────────────────────────────────────────────────────────


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(50))
    resource_id = Column(Integer)
    detail = Column(Text)
    ip_address = Column(String(45))


# ── Engine & Session ────────────────────────────────────────────────────

import threading

_engine = None
_SessionFactory = None
_lock = threading.Lock()


def get_engine():
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = create_engine(Settings.DATABASE_URL, echo=False)
    return _engine


def get_session() -> Session:
    global _SessionFactory
    if _SessionFactory is None:
        with _lock:
            if _SessionFactory is None:
                _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


def init_db() -> None:
    """Create all platform tables."""
    Base.metadata.create_all(get_engine())
