"""Trades API routes.

FastAPI endpoints for trade management operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.container import get_container

router = APIRouter(tags=["trades"])


@router.get("/api/v1/trades", response_model=Dict[str, Any])
async def get_open_trades() -> Dict[str, Any]:
    """Get all currently open trades."""
    container = get_container()
    trade_service = container.get("trade_executor")
    return trade_service.get_open_trades()


@router.post("/api/v1/trades", response_model=Dict[str, Any])
async def open_trade(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
) -> Dict[str, Any]:
    """Open a new trade."""
    container = get_container()
    trade_service = container.get("trade_executor")
    result = trade_service.open_trade(symbol, timeframe)
    return result


@router.delete("/api/v1/trades/{trade_id}")
async def close_trade(
    trade_id: str,
    reason: str = Query("manual", description="Close reason"),
) -> Dict[str, Any]:
    """Close an open trade."""
    container = get_container()
    trade_service = container.get("trade_executor")
    result = trade_service.close_trade(trade_id, reason=reason)
    return result


@router.get("/api/v1/trades/history")
async def get_trade_history(
    start_date: str = Query(None, description="ISO date filter (start)"),
    end_date: str = Query(None, description="ISO date filter (end)"),
) -> Dict[str, Any]:
    """Get trade history with P&L stats."""
    container = get_container()
    trade_service = container.get("trade_executor")
    result = trade_service.get_trade_history(start_date=start_date, end_date=end_date)
    return result