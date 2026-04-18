"""Create default 12 managed signal groups in database."""

from __future__ import annotations

from bots.main_signal_bot.distribution import MANAGED_GROUPS
from database.models import Group
from database.queries import get_session, init_schema


def main() -> None:
    init_schema()
    db = get_session()
    try:
        for item in MANAGED_GROUPS:
            exists = db.query(Group).filter(Group.group_id == item.key).first()
            if exists:
                continue
            db.add(
                Group(
                    name=f"{item.category.title()} {item.grade} {item.audience}",
                    group_id=item.key,
                    group_type=item.audience,
                    category=item.category,
                    max_users=5000,
                    current_users=0,
                    is_active=True,
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
