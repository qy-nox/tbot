"""Payment flow helpers for subscription bot."""

from signal_platform.models import SubscriptionTier
from signal_platform.services.subscription_service import SubscriptionService


def create_pending_payment(db, *, user_id: int, tier: str, provider: str = "manual", period: str = "monthly"):
    return SubscriptionService.create_payment(
        db,
        user_id=user_id,
        tier=SubscriptionTier(tier),
        provider=provider,
        period=period,
    )
