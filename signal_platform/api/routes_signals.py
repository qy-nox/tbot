"""Compatibility signals routes module."""

from fastapi import APIRouter

from signal_platform.api.app import (
    create_signal,
    get_signal,
    list_signals,
    signal_deliveries,
    update_signal_result,
)
from signal_platform.schemas import DeliveryStatusResponse, SignalResponse

router = APIRouter(prefix="/api/signals", tags=["signals"])
router.add_api_route("", list_signals, methods=["GET"], response_model=list[SignalResponse])
router.add_api_route("", create_signal, methods=["POST"], response_model=SignalResponse, status_code=201)
router.add_api_route("/{signal_id}", get_signal, methods=["GET"], response_model=SignalResponse)
router.add_api_route("/{signal_id}/result", update_signal_result, methods=["PATCH"], response_model=SignalResponse)
router.add_api_route("/{signal_id}/deliveries", signal_deliveries, methods=["GET"], response_model=list[DeliveryStatusResponse])

__all__ = ["router"]
