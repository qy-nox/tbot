"""Admin management operations for users/payments/signals."""

from __future__ import annotations

import os

from database.models import Group, Signal, User
from config.settings import is_placeholder_telegram_group_id, is_valid_telegram_chat_id


def list_users(db, limit: int = 20) -> list[User]:
    return db.query(User).order_by(User.id.desc()).limit(limit).all()


def list_signals(db, limit: int = 20) -> list[Signal]:
    return db.query(Signal).order_by(Signal.id.desc()).limit(limit).all()


def list_groups(db) -> list[Group]:
    return db.query(Group).order_by(Group.id.asc()).all()


def add_group(db, *, name: str, group_id: str, group_type: str = "HV", category: str = "crypto") -> Group:
    value = str(group_id).strip()
    if not is_valid_telegram_chat_id(value):
        raise ValueError("group_id must be numeric (example: -1001234567890)")
    if is_placeholder_telegram_group_id(value):
        raise ValueError("group_id cannot be a placeholder example")
    existing = db.query(Group).filter(Group.group_id == value).first()
    if existing:
        return existing
    row = Group(
        name=name,
        group_id=value,
        group_type=group_type,
        category=category,
        max_users=5000,
        current_users=0,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def remove_group(db, *, group_id: str) -> bool:
    row = db.query(Group).filter(Group.group_id == str(group_id).strip()).first()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def test_group_access(*, token: str, group_id: str) -> tuple[bool, str]:
    import requests

    value = str(group_id).strip()
    if not is_valid_telegram_chat_id(value):
        return False, "invalid_format"
    if is_placeholder_telegram_group_id(value):
        return False, "placeholder_id"
    if not token:
        return False, "missing_token"
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getChat",
            params={"chat_id": value},
            timeout=10,
        )
        payload = resp.json() if resp.text else {}
    except requests.RequestException as exc:  # pragma: no cover - network/runtime errors
        return False, str(exc)
    if resp.status_code == 200 and isinstance(payload, dict) and payload.get("ok"):
        title = payload.get("result", {}).get("title") or payload.get("result", {}).get("username") or "ok"
        return True, str(title)
    if isinstance(payload, dict):
        return False, str(payload.get("description", "unknown"))
    return False, "unknown"


def setup_groups(db) -> list[Group]:
    from bots.main_signal_bot.distribution import MANAGED_GROUPS

    created: list[Group] = []
    for index, item in enumerate(MANAGED_GROUPS, start=1):
        group_env = f"SIGNAL_GROUP_{index}_ID"
        group_id = os.getenv(group_env, "").strip()
        if not group_id:
            continue
        row = add_group(
            db,
            name=f"{item.category.title()} {item.grade} {item.audience}",
            group_id=group_id,
            group_type=item.audience,
            category=item.category,
        )
        created.append(row)
    return created
