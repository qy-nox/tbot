"""Compatibility performance routes module."""

from fastapi import APIRouter

from signal_platform.api.app import leaderboard, performance_overview, performance_pairs, win_rates
from signal_platform.schemas import LeaderboardEntry, PairPerformance, PerformanceOverview

router = APIRouter(prefix="/api/performance", tags=["performance"])
router.add_api_route("/overview", performance_overview, methods=["GET"], response_model=PerformanceOverview)
router.add_api_route("/pairs", performance_pairs, methods=["GET"], response_model=list[PairPerformance])
router.add_api_route("/leaderboard", leaderboard, methods=["GET"], response_model=list[LeaderboardEntry])
router.add_api_route("/win-rates", win_rates, methods=["GET"])

__all__ = ["router"]
