# filepath: api/server.py
"""
FastAPI REST Server — exposes trading analysis endpoints.

Run with: python -m api.server
Or: uvicorn api.server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from config import API_PORT, USE_TESTNET
from services.analysis_service import init_analysis_service, get_analysis_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Pydantic Models ---

class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., BTC, BTCUSDT)")
    timeframe: str = Field("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)")


class AnalyzeResponse(BaseModel):
    symbol: str
    timeframe: str
    final_signal: str
    confidence: float
    buy_score: float
    sell_score: float
    hold_score: float
    bot_signals: List[Dict[str, Any]]
    bot_probabilities: Dict[str, Dict[str, float]]
    timestamp: str
    details: Dict[str, Any]


class IndicatorsResponse(BaseModel):
    symbol: str
    timeframe: str
    indicators: Dict[str, Any]


class MarketDataRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field("1h", description="Timeframe")
    limit: int = Field(50, ge=1, le=500, description="Number of candles")


class MarketDataResponse(BaseModel):
    symbol: str
    timeframe: str
    limit: int
    candles: List[Dict[str, float]]


class ErrorResponse(BaseModel):
    error: str


# --- Global service reference ---
_analysis_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize and cleanup."""
    global _analysis_service
    logger.info("Starting FastAPI server...")
    _analysis_service = await init_analysis_service()
    logger.info("Analysis service ready")
    yield
    if _analysis_service:
        await _analysis_service.shutdown()
    logger.info("Server shutdown complete")


app = FastAPI(
    title="Multi-Bot Trading System API",
    description="REST API for multi-bot crypto trading analysis",
    version="0.1.0",
    lifespan=lifespan,
)


def get_service():
    """Get the global analysis service instance."""
    if _analysis_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _analysis_service


# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "testnet": USE_TESTNET}


@app.get("/api/v1/symbols", response_model=Dict[str, List[str]])
async def get_symbols():
    """Get list of supported trading symbols."""
    service = get_service()
    return {"symbols": service.get_supported_symbols()}


@app.get("/api/v1/timeframes", response_model=Dict[str, Dict[str, str]])
async def get_timeframes():
    """Get supported timeframes with descriptions."""
    service = get_service()
    return {"timeframes": service.get_supported_timeframes()}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_coin(request: AnalyzeRequest):
    """
    Full multi-bot analysis for a single coin.

    Returns aggregated signal with confidence and per-bot breakdown.
    """
    service = get_service()
    try:
        result = service.analyze_coin(request.symbol, request.timeframe)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"analyze_coin error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_coin_get(
    symbol: str = Query(..., description="Trading symbol (e.g., BTC, BTCUSDT)"),
    timeframe: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
):
    """GET variant of analyze endpoint for easy browser testing."""
    service = get_service()
    try:
        result = service.analyze_coin(symbol, timeframe)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"analyze_coin error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/indicators", response_model=IndicatorsResponse)
async def get_indicators(request: AnalyzeRequest):
    """Get pre-computed indicator values for a symbol/timeframe."""
    service = get_service()
    try:
        result = service.get_indicators(request.symbol, request.timeframe)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"get_indicators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/indicators", response_model=IndicatorsResponse)
async def get_indicators_get(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
):
    """GET variant of indicators endpoint."""
    service = get_service()
    try:
        result = service.get_indicators(symbol, timeframe)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"get_indicators error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/market-data", response_model=MarketDataResponse)
async def get_market_data(request: MarketDataRequest):
    """Get OHLCV market data for a symbol/timeframe."""
    service = get_service()
    try:
        result = service.get_market_data(request.symbol, request.timeframe, request.limit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"get_market_data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market-data", response_model=MarketDataResponse)
async def get_market_data_get(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
    limit: int = Query(50, ge=1, le=500, description="Number of candles"),
):
    """GET variant of market data endpoint."""
    service = get_service()
    try:
        result = service.get_market_data(symbol, timeframe, limit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"get_market_data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Placeholder endpoints for future tickets (04, 05)
@app.post("/api/v1/trades/open")
async def open_trade(symbol: str, side: str, entry_price: float, sl: float, tp: float):
    raise HTTPException(status_code=501, detail="Not implemented yet - see Ticket 04")


@app.delete("/api/v1/trades/{trade_id}")
async def close_trade(trade_id: str, reason: str = "manual"):
    raise HTTPException(status_code=501, detail="Not implemented yet - see Ticket 04")


@app.get("/api/v1/trades/open")
async def get_open_trades():
    raise HTTPException(status_code=501, detail="Not implemented yet - see Ticket 04")


@app.get("/api/v1/trades/history")
async def get_trade_history(start_date: Optional[str] = None, end_date: Optional[str] = None):
    raise HTTPException(status_code=501, detail="Not implemented yet - see Ticket 04")


@app.post("/api/v1/risk/limit")
async def set_risk_limit(max_daily_loss_eur: float):
    raise HTTPException(status_code=501, detail="Not implemented yet - see Ticket 05")


@app.get("/api/v1/portfolio")
async def get_portfolio():
    raise HTTPException(status_code=501, detail="Not implemented yet - see Ticket 05")


async def main():
    """Run with uvicorn programmatically."""
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=API_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())