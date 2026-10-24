"""Composite provider — tries TradingView first, falls back to local calculation for MFI/ATR."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.domains.indicators.tradingview_provider import TradingViewProvider
from backend.domains.indicators.local_calculator import LocalIndicatorCalculator
from backend.domains.indicators.models import IndicatorValues

logger = logging.getLogger(__name__)


class CompositeProvider(TradingViewProvider):
    """Combines TradingView indicators with local fallback for MFI/ATR."""

    def __init__(self, screener: str = 'crypto', exchange: str = 'BINANCE', timeout: float = 10.0):
        super().__init__(screener=screener, exchange=exchange, timeout=timeout)
        self._local_calc = LocalIndicatorCalculator()

    async def get_indicators(self, symbol: str, timeframe: str, candles: Optional[List[Dict[str, Any]]] = None) -> Optional[IndicatorValues]:
        """Get indicators from TradingView, then fill MFI/ATR from local calculation if needed."""
        tv_result = await super().get_indicators(symbol, timeframe)
        if tv_result is None:
            return None

        if candles and self._local_calc:
            tv_result = self._local_calc.fill_missing(tv_result, candles)

        return tv_result
