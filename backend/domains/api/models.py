"""API domain models.

Defines Pydantic models for API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import status
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request model for analyzing a trading symbol."""
    symbol: str = Field(
        ..., description="Trading symbol (e.g., BTCUSDT, ETHUSDT)"
    )
    timeframe: str = Field(
        "1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"
    )


class AnalyzeResponse(BaseModel):
    """Response model for analysis results."""
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
    """Response model for indicator data."""
    symbol: str
    timeframe: str
    indicators: Dict[str, Any]


class MarketDataRequest(BaseModel):
    """Request model for market data/candles."""
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field("1h", description="Timeframe")
    limit: int = Field(
        50, ge=1, le=500, description="Number of candles to retrieve"
    )


class MarketDataResponse(BaseModel):
    """Response model for market data."""
    symbol: str
    timeframe: str
    limit: int
    candles: List[Dict[str, float]]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int = Field(default=status.HTTP_400_BAD_REQUEST)


class PortfolioResponse(BaseModel):
    """Response model for portfolio status."""
    capital: float
    daily_pnl: float
    open_count: int
    is_halted: bool
    max_open_trades: int
    trade_cooldown_sec: int


class OpenTradeRequest(BaseModel):
    """Request model for opening a trade."""
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field("1h", description="Timeframe")


class OpenTradeResponse(BaseModel):
    """Response model for opening a trade."""
    trade_id: Optional[str] = Field(None, description="Created trade ID")
    symbol: Optional[str] = Field(None, description="Trading symbol")
    side: Optional[str] = Field(None, description="Trade side (long/short)")
    entry_price: Optional[float] = Field(None, description="Entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    quantity: Optional[float] = Field(None, description="Order quantity")
    status: Optional[str] = Field(None, description="Trade status")
    sl_source: Optional[str] = Field(None, description="Stop loss source")
    error: Optional[str] = Field(None, description="Error message if failed")


class TradeHistoryEntry(BaseModel):
    """Single entry in trade history."""
    id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    pnl: float
    pnl_percent: Optional[float] = None
    status: str
    open_time: datetime
    close_time: Optional[datetime] = None
    bot_name: Optional[str] = None
    signal_confidence: Optional[float] = None
