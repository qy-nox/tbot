"""
User management service – registration, authentication, profile updates.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from signal_platform.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from signal_platform.models import AuditLog, SubscriptionTier, User

logger = logging.getLogger(__name__)


class UserService:
    """Stateless helpers – every method receives a ``Session``."""

    # ── Registration ────────────────────────────────────────────────────

    @staticmethod
    def register(
        db: Session,
        *,
        username: str,
        email: str,
        password: str,
        telegram_chat_id: Optional[str] = None,
        tz: str = "UTC",
        language: str = "en",
    ) -> User:
        if db.query(User).filter(User.username == username).first():
            raise ValueError("Username already taken")
        if db.query(User).filter(User.email == email).first():
            raise ValueError("Email already registered")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            telegram_chat_id=telegram_chat_id,
            timezone=tz,
            language=language,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        _audit(db, user.id, "user.register")
        logger.info("Registered user %s (id=%d)", username, user.id)
        return user

    # ── Authentication ──────────────────────────────────────────────────

    @staticmethod
    def authenticate(db: Session, *, username: str, password: str) -> dict:
        user = db.query(User).filter(User.username == username).first()
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account is deactivated")

        user.last_login = datetime.now(timezone.utc)
        db.commit()

        access = create_access_token(user.id, user.username, user.is_admin)
        refresh = create_refresh_token(user.id)

        _audit(db, user.id, "user.login")
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ── Profile ─────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).get(user_id)

    @staticmethod
    def update_profile(db: Session, user_id: int, **fields) -> User:
        user = db.query(User).get(user_id)
        if user is None:
            raise ValueError("User not found")
        for key, value in fields.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
        _audit(db, user_id, "user.update_profile")
        return user

    # ── Admin helpers ───────────────────────────────────────────────────

    @staticmethod
    def list_users(
        db: Session,
        *,
        tier: Optional[SubscriptionTier] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[User]:
        q = db.query(User)
        if tier:
            q = q.filter(User.subscription_tier == tier)
        return q.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def admin_update(
        db: Session,
        user_id: int,
        *,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
    ) -> User:
        user = db.query(User).get(user_id)
        if user is None:
            raise ValueError("User not found")
        if is_active is not None:
            user.is_active = is_active
        if is_admin is not None:
            user.is_admin = is_admin
        if subscription_tier is not None:
            user.subscription_tier = subscription_tier
        db.commit()
        db.refresh(user)
        _audit(db, user_id, "admin.update_user")
        return user

    @staticmethod
    def count_by_tier(db: Session) -> dict:
        """Return user counts grouped by subscription tier."""
        result: dict = {}
        for tier in SubscriptionTier:
            result[tier.value] = (
                db.query(User).filter(User.subscription_tier == tier).count()
            )
        result["total"] = db.query(User).count()
        result["active"] = db.query(User).filter(User.is_active.is_(True)).count()
        return result


# ── Internal helpers ────────────────────────────────────────────────────


def _audit(db: Session, user_id: int, action: str, detail: str | None = None):
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))
    db.commit()
