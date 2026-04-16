"""Additional SQLAlchemy models for groups/channels/subscriptions extensions."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from signal_platform.models import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionRecord(Base):
    __tablename__ = "subscription_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(String(20), nullable=False)
    status = Column(String(20), default="active", nullable=False)
    payment_date = Column(DateTime, default=_utcnow)


class SignalGroup(Base):
    __tablename__ = "signal_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    link = Column(String(255), nullable=False)
    signal_filter = Column(String(50), default="all")
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class ChannelConfig(Base):
    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    channel_type = Column(String(20), nullable=False)
    subscribers = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    revenue_share = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_utcnow)
