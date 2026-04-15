"""
Signal quality grading & enhanced signal service.

Grades
------
- **A+** : confidence ≥ 0.85 *and* historical pair win-rate ≥ 70 %
- **A**  : confidence ≥ 0.75 *or* historical pair win-rate ≥ 60 %
- **B**  : confidence ≥ 0.60
- **C**  : everything else (still sent to VIP users for reference)

Binary signals
--------------
- CALL / PUT direction
- Duration in seconds (30 s, 60 s, 5 min, etc.)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from signal_platform.models import (
    SignalDirection,
    SignalGrade,
    SignalOutcome,
    SignalRecord,
    SignalType,
)

logger = logging.getLogger(__name__)


class SignalService:
    """Create, grade, list, and resolve trading signals."""

    # ── Create ──────────────────────────────────────────────────────────

    @staticmethod
    def create_signal(
        db: Session,
        *,
        signal_type: SignalType = SignalType.CRYPTO,
        pair: str,
        direction: SignalDirection,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit_1: Optional[float] = None,
        take_profit_2: Optional[float] = None,
        take_profit_3: Optional[float] = None,
        confidence: float,
        strategy: Optional[str] = None,
        reason: Optional[str] = None,
        valid_minutes: int = 60,
        binary_duration: Optional[int] = None,
        binary_direction: Optional[str] = None,
    ) -> SignalRecord:
        # Compute risk/reward for crypto signals
        rr = None
        if signal_type == SignalType.CRYPTO and stop_loss and take_profit_1:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit_1 - entry_price)
            rr = round(reward / risk, 2) if risk > 0 else None

        # Auto-grade
        pair_wr = SignalService._pair_win_rate(db, pair)
        grade = _compute_grade(confidence, pair_wr)

        record = SignalRecord(
            signal_type=signal_type,
            pair=pair,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            confidence=confidence,
            grade=grade,
            strategy=strategy,
            reason=reason,
            valid_until=datetime.now(timezone.utc) + timedelta(minutes=valid_minutes),
            risk_reward_ratio=rr,
            binary_duration=binary_duration,
            binary_direction=binary_direction,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "Signal #%d created: %s %s %s grade=%s conf=%.0f%%",
            record.id,
            signal_type.value,
            pair,
            direction.value,
            grade.value if grade else "?",
            confidence * 100,
        )
        return record

    # ── Update outcome ──────────────────────────────────────────────────

    @staticmethod
    def update_outcome(
        db: Session,
        signal_id: int,
        *,
        outcome: SignalOutcome,
        actual_exit_price: Optional[float] = None,
        pnl_percent: Optional[float] = None,
    ) -> SignalRecord:
        sig = db.query(SignalRecord).get(signal_id)
        if sig is None:
            raise ValueError("Signal not found")
        sig.outcome = outcome
        sig.actual_exit_price = actual_exit_price
        sig.pnl_percent = pnl_percent
        sig.closed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(sig)
        return sig

    # ── Queries ─────────────────────────────────────────────────────────

    @staticmethod
    def get_signal(db: Session, signal_id: int) -> Optional[SignalRecord]:
        return db.query(SignalRecord).get(signal_id)

    @staticmethod
    def list_signals(
        db: Session,
        *,
        signal_type: Optional[SignalType] = None,
        pair: Optional[str] = None,
        grade: Optional[SignalGrade] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SignalRecord]:
        q = db.query(SignalRecord)
        if signal_type:
            q = q.filter(SignalRecord.signal_type == signal_type)
        if pair:
            q = q.filter(SignalRecord.pair == pair)
        if grade:
            q = q.filter(SignalRecord.grade == grade)
        return q.order_by(SignalRecord.timestamp.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def list_recent(db: Session, limit: int = 100) -> List[SignalRecord]:
        return (
            db.query(SignalRecord)
            .order_by(SignalRecord.timestamp.desc())
            .limit(limit)
            .all()
        )

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _pair_win_rate(db: Session, pair: str) -> float:
        """Historical win rate for a specific pair (0..1)."""
        total = (
            db.query(func.count(SignalRecord.id))
            .filter(
                SignalRecord.pair == pair,
                SignalRecord.outcome != SignalOutcome.PENDING,
            )
            .scalar()
        )
        if not total:
            return 0.0
        wins = (
            db.query(func.count(SignalRecord.id))
            .filter(
                SignalRecord.pair == pair,
                SignalRecord.outcome.in_([
                    SignalOutcome.TP1_HIT,
                    SignalOutcome.TP2_HIT,
                    SignalOutcome.TP3_HIT,
                ]),
            )
            .scalar()
        )
        return wins / total


# ── Grading helper ──────────────────────────────────────────────────────


def _compute_grade(confidence: float, pair_win_rate: float) -> SignalGrade:
    if confidence >= 0.85 and pair_win_rate >= 0.70:
        return SignalGrade.A_PLUS
    if confidence >= 0.75 or pair_win_rate >= 0.60:
        return SignalGrade.A
    if confidence >= 0.60:
        return SignalGrade.B
    return SignalGrade.C
