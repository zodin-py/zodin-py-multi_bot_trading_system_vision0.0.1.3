"""Local indicator calculator — fallback for MFI/ATR not available via TradingView."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    import pandas_ta as pta
except ImportError:
    pta = None

from backend.domains.indicators.models import IndicatorValues

logger = logging.getLogger(__name__)


class LocalIndicatorCalculator:
    """Computes MFI and ATR locally from OHLCV candles as fallback."""

    def compute_mfi(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float], period: int = 14) -> float:
        if pta is None:
            return 0.0
        try:
            df = __import__('pandas').DataFrame({'high': highs, 'low': lows, 'close': closes, 'volume': volumes})
            result = pta.mfi(df['high'], df['low'], df['close'], df['volume'], length=period)
            return float(result.iloc[-1]) if len(result) > 0 else 0.0
        except Exception as e:
            logger.warning(f'MFI calculation failed: {e}')
            return 0.0

    def compute_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        if pta is None:
            return 0.0
        try:
            df = __import__('pandas').DataFrame({'high': highs, 'low': lows, 'close': closes})
            result = pta.atr(df['high'], df['low'], df['close'], length=period)
            return float(result.iloc[-1]) if len(result) > 0 else 0.0
        except Exception as e:
            logger.warning(f'ATR calculation failed: {e}')
            return 0.0

    def fill_missing(self, tv_values: IndicatorValues, candles: List[Dict[str, Any]]) -> IndicatorValues:
        """Fill MFI and ATR from candles if they are missing in TradingView result."""
        if len(candles) < 15:
            return tv_values

        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        volumes = [c.get('volume', 0) for c in candles]

        if tv_values.mfi == 0.0:
            tv_values.mfi = self.compute_mfi(highs, lows, closes, volumes)
        if tv_values.atr == 0.0:
            tv_values.atr = self.compute_atr(highs, lows, closes)

        return tv_values
