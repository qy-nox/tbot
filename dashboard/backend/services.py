"""Service layer for dashboard backend endpoints."""

from __future__ import annotations

from sqlalchemy import func

from bots.bot_main.market_data import get_live_market_status
from signal_platform.models import Payment, SignalRecord, User
from signal_platform.services.performance_service import PerformanceService
from signal_platform.services.subscription_service import SubscriptionService


def list_users(db):
    return db.query(User).order_by(User.created_at.desc()).limit(200).all()


def list_subscriptions(db):
    return db.query(Payment).order_by(Payment.created_at.desc()).limit(200).all()


def list_signals(db):
    return db.query(SignalRecord).order_by(SignalRecord.timestamp.desc()).limit(200).all()


def market_snapshot():
    return get_live_market_status()


def analytics_overview(db) -> dict[str, float | int]:
    perf = PerformanceService.overview(db)
    return {
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "total_revenue": SubscriptionService.total_revenue(db),
        "win_rate": float(perf["win_rate"]),
    }
