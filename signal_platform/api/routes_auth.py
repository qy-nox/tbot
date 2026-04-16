"""Compatibility auth routes module."""

from fastapi import APIRouter

from signal_platform.api.app import login, refresh, register
from signal_platform.schemas import TokenResponse, UserProfile

router = APIRouter(prefix="/api/auth", tags=["auth"])
router.add_api_route("/register", register, methods=["POST"], response_model=UserProfile, status_code=201)
router.add_api_route("/login", login, methods=["POST"], response_model=TokenResponse)
router.add_api_route("/refresh", refresh, methods=["POST"], response_model=TokenResponse)

__all__ = ["router"]
