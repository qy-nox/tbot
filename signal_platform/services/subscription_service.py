"""
Subscription & payment management service.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from signal_platform.models import (
    AuditLog,
    Payment,
    SubscriptionPlan,
    SubscriptionTier,
    User,
)

logger = logging.getLogger(__name__)

# ── Default plan definitions ────────────────────────────────────────────

DEFAULT_PLANS = [
    {
        "tier": SubscriptionTier.FREE,
        "name": "Free",
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "max_signals_per_day": 3,
        "features": json.dumps([
            "3 signals per day",
            "Crypto signals only",
            "Telegram delivery",
            "Basic analytics",
        ]),
    },
    {
        "tier": SubscriptionTier.PREMIUM,
        "name": "Premium",
        "price_monthly": 29.99,
        "price_yearly": 299.99,
        "max_signals_per_day": 20,
        "features": json.dumps([
            "20 signals per day",
            "Crypto + Binary signals",
            "Telegram + Discord delivery",
            "Full analytics & leaderboards",
            "Signal grades A+ and A",
            "Priority support",
        ]),
    },
    {
        "tier": SubscriptionTier.VIP,
        "name": "VIP",
        "price_monthly": 79.99,
        "price_yearly": 799.99,
        "max_signals_per_day": -1,  # unlimited
        "features": json.dumps([
            "Unlimited signals",
            "All signal types",
            "All delivery channels",
            "Full analytics & leaderboards",
            "All signal grades",
            "API access",
            "1-on-1 support",
            "Early access to new features",
        ]),
    },
]


class SubscriptionService:
    """Manage plans, payments, and tier upgrades."""

    # ── Plan seed ───────────────────────────────────────────────────────

    @staticmethod
    def seed_plans(db: Session) -> None:
        """Insert default plans if they don't exist."""
        for plan_data in DEFAULT_PLANS:
            exists = (
                db.query(SubscriptionPlan)
                .filter(SubscriptionPlan.tier == plan_data["tier"])
                .first()
            )
            if not exists:
                db.add(SubscriptionPlan(**plan_data))
        db.commit()

    # ── List plans ──────────────────────────────────────────────────────

    @staticmethod
    def list_plans(db: Session) -> List[SubscriptionPlan]:
        return (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.is_active.is_(True))
            .all()
        )

    # ── Create payment ──────────────────────────────────────────────────

    @staticmethod
    def create_payment(
        db: Session,
        *,
        user_id: int,
        tier: SubscriptionTier,
        provider: str = "stripe",
        period: str = "monthly",
    ) -> Payment:
        plan = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.tier == tier)
            .first()
        )
        if plan is None:
            raise ValueError(f"Plan not found for tier {tier.value}")

        amount = plan.price_monthly if period == "monthly" else plan.price_yearly
        now = datetime.now(timezone.utc)
        period_end = now + (timedelta(days=30) if period == "monthly" else timedelta(days=365))

        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="USD",
            provider=provider,
            status="pending",
            subscription_tier=tier,
            period_start=now,
            period_end=period_end,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        logger.info(
            "Payment #%d created for user %d: $%.2f %s (%s)",
            payment.id, user_id, amount, tier.value, provider,
        )
        return payment

    # ── Confirm payment (webhook callback) ──────────────────────────────

    @staticmethod
    def confirm_payment(
        db: Session,
        payment_id: int,
        provider_tx_id: str,
    ) -> Payment:
        payment = db.query(Payment).get(payment_id)
        if payment is None:
            raise ValueError("Payment not found")

        payment.status = "completed"
        payment.provider_tx_id = provider_tx_id

        # Upgrade user tier
        user = db.query(User).get(payment.user_id)
        if user and payment.subscription_tier:
            user.subscription_tier = payment.subscription_tier

        db.commit()
        db.refresh(payment)

        db.add(AuditLog(
            user_id=payment.user_id,
            action="payment.confirmed",
            detail=f"tx={provider_tx_id} tier={payment.subscription_tier.value}",
        ))
        db.commit()
        logger.info("Payment #%d confirmed (tx=%s)", payment_id, provider_tx_id)
        return payment

    # ── Billing history ─────────────────────────────────────────────────

    @staticmethod
    def billing_history(
        db: Session, user_id: int, limit: int = 50
    ) -> List[Payment]:
        return (
            db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .all()
        )

    # ── Revenue stats (admin) ───────────────────────────────────────────

    @staticmethod
    def total_revenue(db: Session) -> float:
        from sqlalchemy import func

        result = (
            db.query(func.coalesce(func.sum(Payment.amount), 0.0))
            .filter(Payment.status == "completed")
            .scalar()
        )
        return float(result)

    # ── Subscription expiry check ───────────────────────────────────────

    @staticmethod
    def expire_subscriptions(db: Session) -> int:
        """Downgrade users whose latest payment period has ended."""
        now = datetime.now(timezone.utc)
        expired = (
            db.query(User)
            .filter(
                User.subscription_tier != SubscriptionTier.FREE,
            )
            .all()
        )
        count = 0
        for user in expired:
            latest: Optional[Payment] = (
                db.query(Payment)
                .filter(
                    Payment.user_id == user.id,
                    Payment.status == "completed",
                )
                .order_by(Payment.period_end.desc())
                .first()
            )
            if latest and latest.period_end and latest.period_end < now:
                user.subscription_tier = SubscriptionTier.FREE
                count += 1
                logger.info("User %s subscription expired → free", user.username)

        db.commit()
        return count
