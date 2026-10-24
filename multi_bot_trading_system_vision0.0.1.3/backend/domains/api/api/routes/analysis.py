"""Analysis API routes.

FastAPI endpoints for market analysis operations.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.container import get_container

router = APIRouter(tags=["analysis"])


@router.get("/api/v1/symbols", response_model=Dict[str, List[str]])
async def get_symbols() -> Dict[str, List[str]]:
    """Get supported trading symbols."""
    container = get_container()
    analysis_service = container.get("analysis_service")
    return {"symbols": analysis_service.get_supported_symbols()}


@router.get("/api/v1/timeframes", response_model=Dict[str, Dict[str, str]])
async def get_timeframes() -> Dict[str, Dict[str, str]]:
    """Get supported timeframes."""
    container = get_container()
    analysis_service = container.get("analysis_service")
    return {"timeframes": analysis_service.get_supported_timeframes()}


@router.post("/api/v1/analyze", response_model=Dict[str, Any])
async def analyze_coin(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
) -> Dict[str, Any]:
    """Analyze a trading symbol and return signal."""
    container = get_container()
    analysis_service = container.get("analysis_service")
    result = analysis_service.analyze_coin(symbol, timeframe)
    return result


@router.post("/api/v1/indicators", response_model=Dict[str, Any])
async def get_indicators(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
) -> Dict[str, Any]:
    """Get technical indicators for a symbol."""
    container = get_container()
    analysis_service = container.get("analysis_service")
    result = analysis_service.get_indicators(symbol, timeframe)
    return result


@router.post("/api/v1/market-data", response_model=Dict[str, Any])
async def get_market_data(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
    limit: int = Query(50, ge=1, le=500, description="Number of candles"),
) -> Dict[str, Any]:
    """Get market/candle data for a symbol."""
    container = get_container()
    analysis_service = container.get("analysis_service")
    result = analysis_service.get_market_data(symbol, timeframe, limit)
    return result