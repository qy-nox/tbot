"""FastAPI routes for admin dashboard management views."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dashboard.backend import services
from dashboard.backend.models import (
    DashboardSignal,
    DashboardStats,
    DashboardSubscription,
    DashboardUser,
)
from signal_platform.models import get_session

router = APIRouter(prefix="/dashboard/backend", tags=["dashboard-backend"])


def _db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/users", response_model=list[DashboardUser])
def users(db: Session = Depends(_db)):
    return [
        DashboardUser(
            id=user.id,
            username=user.username,
            tier=user.subscription_tier.value,
            is_active=user.is_active,
        )
        for user in services.list_users(db)
    ]


@router.get("/subscriptions", response_model=list[DashboardSubscription])
def subscriptions(db: Session = Depends(_db)):
    return [
        DashboardSubscription(
            id=payment.id,
            user_id=payment.user_id,
            amount=payment.amount,
            status=payment.status,
            tier=payment.subscription_tier.value if payment.subscription_tier else None,
        )
        for payment in services.list_subscriptions(db)
    ]


@router.get("/signals", response_model=list[DashboardSignal])
def signals(db: Session = Depends(_db)):
    return [
        DashboardSignal(
            id=signal.id,
            pair=signal.pair,
            direction=signal.direction.value,
            grade=signal.grade.value if signal.grade else None,
            confidence=signal.confidence,
        )
        for signal in services.list_signals(db)
    ]


@router.get("/market")
def market():
    return services.market_snapshot()


@router.get("/analytics", response_model=DashboardStats)
def analytics(db: Session = Depends(_db)):
    return DashboardStats.model_validate(services.analytics_overview(db))
