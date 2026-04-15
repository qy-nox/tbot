"""
Database models and utilities using SQLAlchemy.
Stores signals, trades, and performance metrics.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import Settings


def _utcnow() -> datetime:
    """Return the current UTC datetime (used as a column default)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Signal(Base):
    """Recorded trading signal."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=_utcnow)
    pair = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # BUY / SELL
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit_1 = Column(Float)
    take_profit_2 = Column(Float)
    take_profit_3 = Column(Float)
    confidence = Column(Float)
    strategy = Column(String(50))
    reason = Column(Text)

    def __repr__(self) -> str:
        return (
            f"<Signal {self.pair} {self.direction} @ {self.entry_price} "
            f"conf={self.confidence:.0%}>"
        )


class Trade(Base):
    """Executed trade record."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opened_at = Column(DateTime, default=_utcnow)
    closed_at = Column(DateTime)
    pair = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    position_size = Column(Float)
    pnl = Column(Float)
    pnl_pct = Column(Float)
    status = Column(String(10), default="OPEN")  # OPEN / CLOSED

    def __repr__(self) -> str:
        return f"<Trade {self.pair} {self.direction} pnl={self.pnl}>"


class PerformanceMetric(Base):
    """Daily or periodic performance snapshot."""

    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=_utcnow)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    current_balance = Column(Float)


# ── Engine & session factory ────────────────────────────────────────────

_engine = None
_SessionFactory = None


def get_engine():
    """Return (and lazily create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(Settings.DATABASE_URL, echo=False)
    return _engine


def get_session() -> Session:
    """Return a new database session."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory()


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(get_engine())
