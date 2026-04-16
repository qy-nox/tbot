"""Compatibility subscriptions routes module."""

from fastapi import APIRouter

from signal_platform.api.app import billing_history, confirm_payment, create_payment, list_plans
from signal_platform.schemas import CreatePaymentRequest, PaymentResponse, SubscriptionPlanResponse

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])
router.add_api_route("/plans", list_plans, methods=["GET"], response_model=list[SubscriptionPlanResponse])
router.add_api_route("/payments", create_payment, methods=["POST"], response_model=PaymentResponse, status_code=201)
router.add_api_route("/payments/{payment_id}/confirm", confirm_payment, methods=["POST"], response_model=PaymentResponse)
router.add_api_route("/billing", billing_history, methods=["GET"], response_model=list[PaymentResponse])

__all__ = ["router", "CreatePaymentRequest"]
