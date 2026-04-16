"""
FastAPI application – Professional Trading Signal Service Platform API.

Routes
------
/api/auth       – register, login, refresh
/api/users      – profile, update
/api/signals    – CRUD, list, outcome update
/api/performance – overview, per-pair, leaderboard
/api/subscriptions – plans, payments, billing
/api/admin      – dashboard, user management, signal management
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from signal_platform.auth import decode_token
from dashboard.backend.api import router as dashboard_backend_router
from signal_platform.models import (
    SignalGrade,
    SignalOutcome,
    SignalType,
    SubscriptionTier,
    get_session,
    init_db,
)
from signal_platform.dashboard import router as dashboard_router
from signal_platform.schemas import (
    AdminDashboard,
    AdminUserUpdate,
    CreatePaymentRequest,
    DeliveryStatusResponse,
    LeaderboardEntry,
    LoginRequest,
    PairPerformance,
    PaymentResponse,
    PerformanceOverview,
    RefreshRequest,
    RegisterRequest,
    SignalCreate,
    SignalResponse,
    SignalResultUpdate,
    SubscriptionPlanResponse,
    TokenResponse,
    UserProfile,
    UserUpdate,
)
from signal_platform.services.distribution_service import DistributionService
from signal_platform.services.performance_service import PerformanceService
from signal_platform.services.signal_service import SignalService
from signal_platform.services.subscription_service import SubscriptionService
from signal_platform.services.user_service import UserService

logger = logging.getLogger(__name__)

# ── Lifespan ────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Startup
    init_db()
    db = get_session()
    try:
        SubscriptionService.seed_plans(db)
    finally:
        db.close()
    yield
    # Shutdown (nothing to clean up)


# ── App factory ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Trading Signal Service Platform",
    description="Professional SAAS platform for crypto & binary trading signal distribution.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dashboard_router)
app.include_router(dashboard_backend_router)


# ── Dependencies ────────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def _db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def _current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(_db),
):
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(creds.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = UserService.get_by_id(db, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def _admin_user(user=Depends(_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ═══════════════════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════════════════


@app.post("/api/auth/register", response_model=UserProfile, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(_db)):
    try:
        user = UserService.register(
            db,
            username=body.username,
            email=body.email,
            password=body.password,
            telegram_chat_id=body.telegram_chat_id,
            tz=body.timezone,
            language=body.language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(_db)):
    try:
        tokens = UserService.authenticate(db, username=body.username, password=body.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return tokens


@app.post("/api/auth/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(_db)):
    try:
        payload = decode_token(body.refresh_token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    user = UserService.get_by_id(db, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    from signal_platform.auth import create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES

    return {
        "access_token": create_access_token(user.id, user.username, user.is_admin),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ═══════════════════════════════════════════════════════════════════════
#  USER PROFILE
# ═══════════════════════════════════════════════════════════════════════


@app.get("/api/users/me", response_model=UserProfile)
def get_me(user=Depends(_current_user)):
    return user


@app.patch("/api/users/me", response_model=UserProfile)
def update_me(body: UserUpdate, user=Depends(_current_user), db: Session = Depends(_db)):
    updated = UserService.update_profile(db, user.id, **body.model_dump(exclude_unset=True))
    return updated


# ═══════════════════════════════════════════════════════════════════════
#  SIGNALS
# ═══════════════════════════════════════════════════════════════════════


@app.post("/api/signals", response_model=SignalResponse, status_code=201)
def create_signal(body: SignalCreate, user=Depends(_admin_user), db: Session = Depends(_db)):
    sig = SignalService.create_signal(
        db,
        signal_type=body.signal_type,
        pair=body.pair,
        direction=body.direction,
        entry_price=body.entry_price,
        stop_loss=body.stop_loss,
        take_profit_1=body.take_profit_1,
        take_profit_2=body.take_profit_2,
        take_profit_3=body.take_profit_3,
        confidence=body.confidence,
        strategy=body.strategy,
        reason=body.reason,
        valid_minutes=body.valid_minutes,
        binary_duration=body.binary_duration,
        binary_direction=body.binary_direction,
    )
    # Distribute to users
    DistributionService.distribute(db, sig)
    return sig


@app.get("/api/signals", response_model=List[SignalResponse])
def list_signals(
    signal_type: Optional[SignalType] = None,
    pair: Optional[str] = None,
    grade: Optional[SignalGrade] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user=Depends(_current_user),
    db: Session = Depends(_db),
):
    return SignalService.list_signals(
        db, signal_type=signal_type, pair=pair, grade=grade, limit=limit, offset=offset,
    )


@app.get("/api/signals/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: int, user=Depends(_current_user), db: Session = Depends(_db)):
    sig = SignalService.get_signal(db, signal_id)
    if sig is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return sig


@app.patch("/api/signals/{signal_id}/result", response_model=SignalResponse)
def update_signal_result(
    signal_id: int,
    body: SignalResultUpdate,
    user=Depends(_admin_user),
    db: Session = Depends(_db),
):
    try:
        return SignalService.update_outcome(
            db, signal_id, outcome=body.outcome,
            actual_exit_price=body.actual_exit_price, pnl_percent=body.pnl_percent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/signals/{signal_id}/deliveries", response_model=List[DeliveryStatusResponse])
def signal_deliveries(signal_id: int, user=Depends(_admin_user), db: Session = Depends(_db)):
    return DistributionService.delivery_status(db, signal_id)


# ═══════════════════════════════════════════════════════════════════════
#  PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════


@app.get("/api/performance/overview", response_model=PerformanceOverview)
def performance_overview(
    days: Optional[int] = None,
    user=Depends(_current_user),
    db: Session = Depends(_db),
):
    return PerformanceService.overview(db, days=days)


@app.get("/api/performance/pairs", response_model=List[PairPerformance])
def performance_pairs(user=Depends(_current_user), db: Session = Depends(_db)):
    return PerformanceService.per_pair(db)


@app.get("/api/performance/leaderboard", response_model=List[LeaderboardEntry])
def leaderboard(
    top_n: int = Query(10, ge=1, le=50),
    user=Depends(_current_user),
    db: Session = Depends(_db),
):
    return PerformanceService.leaderboard(db, top_n=top_n)


@app.get("/api/performance/win-rates")
def win_rates(user=Depends(_current_user), db: Session = Depends(_db)):
    return PerformanceService.win_rate_by_period(db)


# ═══════════════════════════════════════════════════════════════════════
#  SUBSCRIPTIONS & PAYMENTS
# ═══════════════════════════════════════════════════════════════════════


@app.get("/api/subscriptions/plans", response_model=List[SubscriptionPlanResponse])
def list_plans(db: Session = Depends(_db)):
    return SubscriptionService.list_plans(db)


@app.post("/api/subscriptions/payments", response_model=PaymentResponse, status_code=201)
def create_payment(body: CreatePaymentRequest, user=Depends(_current_user), db: Session = Depends(_db)):
    try:
        return SubscriptionService.create_payment(
            db, user_id=user.id, tier=body.tier, provider=body.provider, period=body.period,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/subscriptions/payments/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(payment_id: int, provider_tx_id: str, user=Depends(_admin_user), db: Session = Depends(_db)):
    try:
        return SubscriptionService.confirm_payment(db, payment_id, provider_tx_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/subscriptions/billing", response_model=List[PaymentResponse])
def billing_history(user=Depends(_current_user), db: Session = Depends(_db)):
    return SubscriptionService.billing_history(db, user.id)


# ═══════════════════════════════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════════════════════════════


@app.get("/api/admin/dashboard", response_model=AdminDashboard)
def admin_dashboard(user=Depends(_admin_user), db: Session = Depends(_db)):
    counts = UserService.count_by_tier(db)
    overview = PerformanceService.overview(db, days=7)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    from signal_platform.models import SignalRecord
    today_signals = (
        db.query(SignalRecord).filter(SignalRecord.timestamp >= today).count()
    )
    return {
        "total_users": counts["total"],
        "active_users": counts["active"],
        "premium_users": counts.get("premium", 0),
        "vip_users": counts.get("vip", 0),
        "total_signals_today": today_signals,
        "total_revenue": SubscriptionService.total_revenue(db),
        "win_rate_7d": overview["win_rate"],
        "pending_signals": overview["pending"],
    }


@app.get("/api/admin/users", response_model=List[UserProfile])
def admin_list_users(
    tier: Optional[SubscriptionTier] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user=Depends(_admin_user),
    db: Session = Depends(_db),
):
    return UserService.list_users(db, tier=tier, offset=offset, limit=limit)


@app.patch("/api/admin/users/{user_id}", response_model=UserProfile)
def admin_update_user(
    user_id: int,
    body: AdminUserUpdate,
    user=Depends(_admin_user),
    db: Session = Depends(_db),
):
    try:
        return UserService.admin_update(
            db, user_id,
            is_active=body.is_active, is_admin=body.is_admin,
            subscription_tier=body.subscription_tier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/admin/deliveries/retry")
def retry_deliveries(user=Depends(_admin_user), db: Session = Depends(_db)):
    count = DistributionService.retry_failed(db)
    return {"retried": count}


@app.post("/api/admin/performance/snapshot")
def create_snapshot(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    user=Depends(_admin_user),
    db: Session = Depends(_db),
):
    snap = PerformanceService.generate_snapshot(db, period=period)
    return {"id": snap.id, "period": snap.period, "win_rate": snap.win_rate}


# ═══════════════════════════════════════════════════════════════════════
#  HEALTH
# ═══════════════════════════════════════════════════════════════════════


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Trading Signal Platform", "version": "1.0.0"}
