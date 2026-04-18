"""Reusable query helpers for the ecosystem database models."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import Settings
from database.models import Base, Group, Payment, PaymentQueue, Signal, Subscription, User

_engine = create_engine(Settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def init_schema() -> None:
    """Create all compatibility tables."""
    Base.metadata.create_all(_engine)


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    return SessionLocal()


def get_user_by_telegram_id(db: Session, telegram_id: str) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def list_active_groups(db: Session) -> list[Group]:
    return db.query(Group).filter(Group.is_active.is_(True)).all()


def create_signal(db: Session, **kwargs) -> Signal:
    signal = Signal(**kwargs)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


def queue_payment_verification(db: Session, *, user_id: int, payment_id: int) -> PaymentQueue:
    row = PaymentQueue(user_id=user_id, payment_id=payment_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_user_subscriptions(db: Session, user_id: int) -> list[Subscription]:
    return db.query(Subscription).filter(Subscription.user_id == user_id).all()


def list_pending_payments(db: Session) -> list[Payment]:
    return db.query(Payment).filter(Payment.status == "pending").all()
