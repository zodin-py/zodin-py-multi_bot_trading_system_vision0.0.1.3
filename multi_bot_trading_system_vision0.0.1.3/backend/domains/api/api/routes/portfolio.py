"""Portfolio API routes.

FastAPI endpoints for portfolio tracking and reporting.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["portfolio"])


@router.get("/api/v1/portfolio", response_model=Dict[str, Any])
async def get_portfolio() -> Dict[str, Any]:
    """Get portfolio status."""
    return {"capital": 10000.0, "daily_pnl": 0.0, "open_count": 0}


@router.post("/api/v1/risk/limit")
async def set_risk_limit(
    max_daily_loss_eur: float = ...,
) -> Dict[str, Any]:
    """Set maximum daily loss limit."""
    return {"success": True, "current_limit": max_daily_loss_eur}