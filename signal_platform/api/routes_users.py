"""Compatibility users routes module."""

from fastapi import APIRouter

from signal_platform.api.app import get_me, update_me
from signal_platform.schemas import UserProfile

router = APIRouter(prefix="/api/users", tags=["users"])
router.add_api_route("/me", get_me, methods=["GET"], response_model=UserProfile)
router.add_api_route("/me", update_me, methods=["PATCH"], response_model=UserProfile)

__all__ = ["router"]
