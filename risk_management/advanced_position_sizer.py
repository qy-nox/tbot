"""Advanced position sizing facade."""

from __future__ import annotations

from risk_management.position_sizer import PositionPlan, PositionSizer


class AdvancedPositionSizer(PositionSizer):
    def compute_dynamic(self, *args, confidence: float = 1.0, **kwargs) -> PositionPlan | None:
        return self.compute(*args, confidence=max(0.25, min(confidence, 1.0)), **kwargs)
