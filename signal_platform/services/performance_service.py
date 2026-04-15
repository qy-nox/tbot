"""
Performance analytics service – win rates, ROI, leaderboards.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from signal_platform.models import (
    PerformanceSnapshot,
    SignalOutcome,
    SignalRecord,
)

logger = logging.getLogger(__name__)

_WIN_OUTCOMES = {SignalOutcome.TP1_HIT, SignalOutcome.TP2_HIT, SignalOutcome.TP3_HIT}
_LOSS_OUTCOMES = {SignalOutcome.SL_HIT}
_RESOLVED = _WIN_OUTCOMES | _LOSS_OUTCOMES | {SignalOutcome.EXPIRED, SignalOutcome.CANCELLED}


class PerformanceService:
    """Compute & cache performance metrics."""

    # ── Overall overview ────────────────────────────────────────────────

    @staticmethod
    def overview(db: Session, days: Optional[int] = None) -> dict:
        q = db.query(SignalRecord)
        if days:
            since = datetime.now(timezone.utc) - timedelta(days=days)
            q = q.filter(SignalRecord.timestamp >= since)

        total = q.count()
        winning = q.filter(SignalRecord.outcome.in_(_WIN_OUTCOMES)).count()
        losing = q.filter(SignalRecord.outcome.in_(_LOSS_OUTCOMES)).count()
        pending = q.filter(SignalRecord.outcome == SignalOutcome.PENDING).count()
        resolved = winning + losing

        pnl_sum = (
            db.query(func.coalesce(func.sum(SignalRecord.pnl_percent), 0.0))
            .filter(SignalRecord.outcome.in_(_RESOLVED))
        )
        if days:
            since = datetime.now(timezone.utc) - timedelta(days=days)
            pnl_sum = pnl_sum.filter(SignalRecord.timestamp >= since)
        total_pnl = float(pnl_sum.scalar())

        best = (
            db.query(func.max(SignalRecord.pnl_percent))
            .filter(SignalRecord.outcome.in_(_RESOLVED))
            .scalar()
        )
        worst = (
            db.query(func.min(SignalRecord.pnl_percent))
            .filter(SignalRecord.outcome.in_(_RESOLVED))
            .scalar()
        )

        return {
            "total_signals": total,
            "winning": winning,
            "losing": losing,
            "pending": pending,
            "win_rate": round(winning / resolved, 4) if resolved else 0.0,
            "total_pnl_percent": round(total_pnl, 2),
            "avg_pnl_percent": round(total_pnl / resolved, 2) if resolved else 0.0,
            "best_signal_pnl": best,
            "worst_signal_pnl": worst,
        }

    # ── Per-pair performance ────────────────────────────────────────────

    @staticmethod
    def per_pair(db: Session) -> List[dict]:
        pairs = (
            db.query(SignalRecord.pair)
            .distinct()
            .all()
        )
        results = []
        for (pair,) in pairs:
            total = (
                db.query(func.count(SignalRecord.id))
                .filter(
                    SignalRecord.pair == pair,
                    SignalRecord.outcome.in_(_RESOLVED),
                )
                .scalar()
            )
            wins = (
                db.query(func.count(SignalRecord.id))
                .filter(
                    SignalRecord.pair == pair,
                    SignalRecord.outcome.in_(_WIN_OUTCOMES),
                )
                .scalar()
            )
            pnl = (
                db.query(func.coalesce(func.sum(SignalRecord.pnl_percent), 0.0))
                .filter(
                    SignalRecord.pair == pair,
                    SignalRecord.outcome.in_(_RESOLVED),
                )
                .scalar()
            )
            results.append({
                "pair": pair,
                "total_signals": total,
                "win_rate": round(wins / total, 4) if total else 0.0,
                "avg_pnl_percent": round(float(pnl) / total, 2) if total else 0.0,
            })
        return sorted(results, key=lambda r: r["win_rate"], reverse=True)

    # ── Leaderboard (top pairs by win rate) ─────────────────────────────

    @staticmethod
    def leaderboard(db: Session, top_n: int = 10) -> List[dict]:
        data = PerformanceService.per_pair(db)
        # Only include pairs with at least 5 resolved signals
        qualified = [d for d in data if d["total_signals"] >= 5]
        return qualified[:top_n]

    # ── Snapshot generation (to be called periodically) ─────────────────

    @staticmethod
    def generate_snapshot(
        db: Session, period: str = "daily"
    ) -> PerformanceSnapshot:
        now = datetime.now(timezone.utc)
        if period == "daily":
            start = now - timedelta(days=1)
        elif period == "weekly":
            start = now - timedelta(weeks=1)
        else:
            start = now - timedelta(days=30)

        overview = PerformanceService.overview(db)
        snap = PerformanceSnapshot(
            period=period,
            period_start=start,
            period_end=now,
            total_signals=overview["total_signals"],
            winning_signals=overview["winning"],
            losing_signals=overview["losing"],
            win_rate=overview["win_rate"],
            total_pnl_percent=overview["total_pnl_percent"],
            avg_pnl_percent=overview["avg_pnl_percent"],
            best_signal_pnl=overview["best_signal_pnl"],
            worst_signal_pnl=overview["worst_signal_pnl"],
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        return snap

    # ── Win-rate by time window ─────────────────────────────────────────

    @staticmethod
    def win_rate_by_period(db: Session) -> Dict[str, float]:
        """Return win rates for 1d, 7d, 30d windows."""
        result: Dict[str, float] = {}
        for label, days in [("1d", 1), ("7d", 7), ("30d", 30)]:
            ov = PerformanceService.overview(db, days=days)
            result[label] = ov["win_rate"]
        return result
