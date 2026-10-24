"""Indicator service — unified interface for fetching indicators."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.domains.indicators.composite_provider import CompositeProvider
from backend.domains.indicators.models import IndicatorValues

logger = logging.getLogger(__name__)


class IndicatorService:
    """Unified service for indicator fetching."""

    def __init__(self, provider: Optional[CompositeProvider] = None):
        self._provider = provider or CompositeProvider()

    async def get_indicators(self, symbol: str, timeframe: str, candles: Optional[List[Dict[str, Any]]] = None) -> Optional[IndicatorValues]:
        """Get all indicators for symbol/timeframe from TradingView + local fallback."""
        return await self._provider.get_indicators(symbol, timeframe, candles)

    def get_rsi(self, indicators: IndicatorValues) -> float:
        return indicators.rsi

    def get_macd(self, indicators: IndicatorValues) -> Dict[str, float]:
        return {'macd': indicators.macd, 'signal': indicators.macd_signal, 'hist': indicators.macd_hist}

    def get_mfi(self, indicators: IndicatorValues) -> float:
        return indicators.mfi

    def get_adx(self, indicators: IndicatorValues) -> Dict[str, float]:
        return {'adx': indicators.adx, 'plus_di': indicators.plus_di, 'minus_di': indicators.minus_di}

    def get_atr(self, indicators: IndicatorValues) -> float:
        return indicators.atr
