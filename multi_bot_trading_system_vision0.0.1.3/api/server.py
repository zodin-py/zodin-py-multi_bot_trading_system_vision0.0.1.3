# filepath: api/server.py
"""
FastAPI REST Server — exposes trading analysis and execution endpoints.

Run with: python -m api.server
Or: uvicorn api.server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from config import API_PORT, USE_TESTNET
from services.analysis_service import init_analysis_service, get_analysis_service
from services.trade_service import get_trade_service, init_trade_service
from execution.executor import TradeExecutor

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


class OpenTradeResponse(BaseModel):
    trade_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: Optional[float] = None
    status: Optional[str] = None
    sl_source: Optional[str] = None
    error: Optional[str] = None


class PortfolioResponse(BaseModel):
    capital: float
    daily_pnl: float
    open_count: int
    is_halted: bool
    max_open_trades: int
    trade_cooldown_sec: int


# --- Global state ---
_analysis_service = None
_trade_service = None
_executor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize services."""
    global _analysis_service, _trade_service, _executor

    logger.info("Starting FastAPI server...")
    _analysis_service = await init_analysis_service()
    _executor = TradeExecutor()
    _trade_service = init_trade_service(
        _analysis_service.market_data, _executor, _analysis_service.provider
    )
    logger.info("Analysis and trade services ready")
    yield
    if _analysis_service:
        await _analysis_service.shutdown()
    logger.info("Server shutdown complete")


app = FastAPI(
    title="Multi-Bot Trading System API",
    description="REST API for multi-bot crypto trading analysis and execution",
    version="0.1.0",
    lifespan=lifespan,
)


def get_service():
    if _analysis_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return _analysis_service


def get_ts():
    if _trade_service is None:
        raise HTTPException(status_code=503, detail="Trade service not initialized")
    return _trade_service


# ==================== Health & Symbols ====================

@app.get("/health")
async def health_check():
    return {"status": "ok", "testnet": USE_TESTNET}


@app.get("/api/v1/symbols", response_model=Dict[str, List[str]])
async def get_symbols():
    return {"symbols": get_service().get_supported_symbols()}


@app.get("/api/v1/timeframes", response_model=Dict[str, Dict[str, str]])
async def get_timeframes():
    return {"timeframes": get_service().get_supported_timeframes()}


# ==================== Analysis ====================

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_coin(request: AnalyzeRequest):
    try:
        return get_service().analyze_coin(request.symbol, request.timeframe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"analyze_coin error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_coin_get(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
):
    try:
        return get_service().analyze_coin(symbol, timeframe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/indicators", response_model=IndicatorsResponse)
async def get_indicators(request: AnalyzeRequest):
    try:
        return get_service().get_indicators(request.symbol, request.timeframe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/indicators", response_model=IndicatorsResponse)
async def get_indicators_get(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
):
    try:
        return get_service().get_indicators(symbol, timeframe)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/market-data", response_model=MarketDataResponse)
async def get_market_data(request: MarketDataRequest):
    try:
        return get_service().get_market_data(request.symbol, request.timeframe, request.limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/market-data", response_model=MarketDataResponse)
async def get_market_data_get(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
    limit: int = Query(50, ge=1, le=500, description="Number of candles"),
):
    try:
        return get_service().get_market_data(symbol, timeframe, limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Trade endpoints (Ticket 04) ====================

@app.post("/api/v1/trades", response_model=Dict[str, Any])
async def open_trade(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1h", description="Timeframe"),
):
    """
    Open a new trade. Runs full analysis; executes only if confidence >= 65%.
    Places a real market order on Binance Testnet via ccxt.
    """
    try:
        result = get_ts().open_trade(symbol, timeframe)
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"open_trade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/trades/{trade_id}")
async def close_trade(trade_id: str, reason: str = Query("manual")):
    """Close an open trade at the current market price."""
    try:
        result = get_ts().close_trade(trade_id, reason=reason)
        if 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"close_trade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trades", response_model=Dict[str, Any])
async def get_open_trades():
    """Get all currently open trades."""
    return get_ts().get_open_trades()


@app.get("/api/v1/trades/history")
async def get_trade_history(
    start_date: Optional[str] = Query(None, description="ISO date filter (start)"),
    end_date: Optional[str] = Query(None, description="ISO date filter (end)"),
):
    """Get trade history with P&L stats."""
    return get_ts().get_trade_history(start_date=start_date, end_date=end_date)


@app.get("/api/v1/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """Get portfolio status."""
    return get_ts().get_portfolio()


@app.post("/api/v1/risk/limit")
async def set_risk_limit(max_daily_loss_eur: float = Query(..., gt=0)):
    """Set maximum daily loss limit."""
    import config
    config.MAX_DAILY_LOSS = max_daily_loss_eur
    return {"success": True, "current_limit": max_daily_loss_eur}


# ==================== Main ====================

async def main():
    """Run with uvicorn programmatically."""
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=API_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
