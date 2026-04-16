"""Compatibility admin routes module."""

from fastapi import APIRouter

from signal_platform.api.app import (
    admin_dashboard,
    admin_list_users,
    admin_update_user,
    create_snapshot,
    retry_deliveries,
)
from signal_platform.schemas import AdminDashboard, AdminUserUpdate, UserProfile

router = APIRouter(prefix="/api/admin", tags=["admin"])
router.add_api_route("/dashboard", admin_dashboard, methods=["GET"], response_model=AdminDashboard)
router.add_api_route("/users", admin_list_users, methods=["GET"], response_model=list[UserProfile])
router.add_api_route("/users/{user_id}", admin_update_user, methods=["PATCH"], response_model=UserProfile)
router.add_api_route("/deliveries/retry", retry_deliveries, methods=["POST"])
router.add_api_route("/performance/snapshot", create_snapshot, methods=["POST"])

__all__ = ["router", "AdminUserUpdate"]
