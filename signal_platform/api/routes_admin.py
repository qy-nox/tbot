"""Admin website API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from signal_platform.models import SignalRecord, User, get_session

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def get_db_session():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/signals")
def get_signals(db: Session = Depends(get_db_session)):
    """Get all signals."""
    signals = db.query(SignalRecord).order_by(SignalRecord.timestamp.desc()).limit(100).all()
    return {"signals": [s.to_dict() for s in signals]}


@router.get("/users")
def get_users(db: Session = Depends(get_db_session)):
    """Get all users."""
    users = db.query(User).all()
    return {"users": [u.to_dict() for u in users]}


@router.post("/signals/{signal_id}/approve")
def approve_signal(signal_id: int, db: Session = Depends(get_db_session)):
    """Approve a signal."""
    signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    signal.approved = True
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to approve signal %s", signal_id)
        raise HTTPException(status_code=500, detail="Failed to approve signal") from exc
    return {"status": "approved"}
