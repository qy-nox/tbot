"""Initialize all platform database tables and default plans."""

from signal_platform.models import init_db, get_session
from signal_platform.services.subscription_service import SubscriptionService


def main() -> None:
    init_db()
    db = get_session()
    try:
        SubscriptionService.seed_plans(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
