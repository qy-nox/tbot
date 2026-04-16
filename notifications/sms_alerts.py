"""SMS alert stubs."""

from __future__ import annotations


def send_sms(to_number: str, message: str) -> dict:
    return {"to": to_number, "message": message, "status": "queued"}
