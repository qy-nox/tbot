"""Admin website API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from signal_platform.models import SignalRecord, User, get_session

router = APIRouter(prefix="/admin", tags=["admin"])


def _db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/signals")
def get_signals(db: Session = Depends(_db)):
    """Get all signals."""
    signals = db.query(SignalRecord).order_by(SignalRecord.timestamp.desc()).limit(100).all()
    return {"signals": [s.to_dict() for s in signals]}


@router.get("/users")
def get_users(db: Session = Depends(_db)):
    """Get all users."""
    users = db.query(User).all()
    return {"users": [u.to_dict() for u in users]}


@router.post("/signals/{signal_id}/approve")
def approve_signal(signal_id: int, db: Session = Depends(_db)):
    """Approve a signal."""
    signal = db.query(SignalRecord).filter(SignalRecord.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    signal.approved = True
    db.commit()
    return {"status": "approved"}
