"""Auto-group distribution helpers for the 12 required signal groups."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManagedGroup:
    """Definition for a managed Telegram signal group."""

    key: str
    category: str
    grade: str
    audience: str


MANAGED_GROUPS: tuple[ManagedGroup, ...] = (
    ManagedGroup("crypto_b_hv", "crypto", "B", "HV"),
    ManagedGroup("crypto_b_vip", "crypto", "B", "VIP"),
    ManagedGroup("crypto_a_hv", "crypto", "A", "HV"),
    ManagedGroup("crypto_a_vip", "crypto", "A", "VIP"),
    ManagedGroup("crypto_ap_hv", "crypto", "A+", "HV"),
    ManagedGroup("crypto_ap_vip", "crypto", "A+", "VIP"),
    ManagedGroup("binary_b_hv", "binary", "B", "HV"),
    ManagedGroup("binary_b_vip", "binary", "B", "VIP"),
    ManagedGroup("binary_a_hv", "binary", "A", "HV"),
    ManagedGroup("binary_a_vip", "binary", "A", "VIP"),
    ManagedGroup("binary_ap_hv", "binary", "A+", "HV"),
    ManagedGroup("binary_ap_vip", "binary", "A+", "VIP"),
)


def target_groups(*, signal_type: str, grade: str) -> list[ManagedGroup]:
    """Return groups matching signal type and grade."""
    return [g for g in MANAGED_GROUPS if g.category == signal_type and g.grade == grade]
