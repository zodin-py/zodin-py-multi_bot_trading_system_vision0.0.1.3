from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class IndicatorValues(BaseModel):
    """Container for all technical indicator values for one (symbol, timeframe)."""

    symbol: str
    timeframe: str
    timestamp_ms: int
    candle_count: int = 0

    # Core oscillators
    rsi: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    mfi: float = 0.0
    adx: float = 0.0
    plus_di: float = 0.0
    minus_di: float = 0.0
    atr: float = 0.0

    # Moving averages
    ema_9: float = 0.0
    ema_21: float = 0.0
    ema_50: float = 0.0
    ema_200: float = 0.0
    sma_20: float = 0.0
    sma_50: float = 0.0

    # Derived indicators
    stoch_k: float = 0.0
    stoch_d: float = 0.0
    bb_lower: float = 0.0
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    cci: float = 0.0
    momentum: float = 0.0

    # Raw OHLCV (for strategy bots)
    close: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    volume: float = 0.0

    # Extra fields (pivots, Ichimoku, etc.)
    extra: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'timestamp_ms': self.timestamp_ms,
            'candle_count': self.candle_count,
            'rsi': self.rsi,
            'macd': self.macd,
            'macd_signal': self.macd_signal,
            'macd_hist': self.macd_hist,
            'mfi': self.mfi,
            'adx': self.adx,
            'plus_di': self.plus_di,
            'minus_di': self.minus_di,
            'atr': self.atr,
            'ema_9': self.ema_9,
            'ema_21': self.ema_21,
            'ema_50': self.ema_50,
            'ema_200': self.ema_200,
            'sma_20': self.sma_20,
            'sma_50': self.sma_50,
            'stoch_k': self.stoch_k,
            'stoch_d': self.stoch_d,
            'bb_lower': self.bb_lower,
            'bb_upper': self.bb_upper,
            'bb_middle': self.bb_middle,
            'cci': self.cci,
            'momentum': self.momentum,
            'close': self.close,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            **self.extra,
        }
