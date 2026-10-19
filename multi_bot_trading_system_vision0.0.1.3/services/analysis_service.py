# filepath: services/analysis_service.py
"""
Analysis Service — shared business logic for MCP tools and REST endpoints.

This is the single source of truth for coin analysis. Both the MCP server
and the FastAPI REST server delegate to this module.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from aggregator.brain import AggregatedSignal, Brain, SignalType
from bots.base_bot import Signal
from config import COINS, TIMEFRAMES, USE_TESTNET
from data.market_data import MarketData
from indicators.calculator import IndicatorCalculator
from indicators.provider import IndicatorProviderAdapter
from indicators import RSIBot, MACDBot, MFIBot
from bots import SRBot, SMCBot, HarmonicBot, TrendBot

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Centralized analysis service that coordinates:
    - Market data fetching (via MarketData + DuckDB cache)
    - Indicator computation (via IndicatorCalculator)
    - Bot signal generation (RSI, MACD, MFI, SR, SMC, Harmonic, Trend)
    - Signal aggregation (via Brain)
    """

    def __init__(
        self,
        market_data: MarketData,
        calculator: IndicatorCalculator,
    ):
        self.market_data = market_data
        self.calculator = calculator

        # Build provider that bridges MarketData + Calculator
        self.provider = IndicatorProviderAdapter(market_data, calculator)

        # Initialize all 7 bots with the provider
        self.bots = [
            RSIBot(provider=self.provider),
            MACDBot(provider=self.provider),
            MFIBot(provider=self.provider),
            SRBot(provider=self.provider),
            SMCBot(provider=self.provider),
            HarmonicBot(provider=self.provider),
            TrendBot(provider=self.provider),
        ]

        # Brain aggregates bot signals
        self.brain = Brain(self.bots)

    async def initialize(self) -> None:
        """Initialize market data connections (REST + WebSocket)."""
        self.market_data.start()
        logger.info("AnalysisService initialized")

    async def shutdown(self) -> None:
        """Cleanup connections."""
        self.market_data.stop()
        logger.info("AnalysisService shutdown complete")

    def analyze_coin(
        self,
        symbol: str,
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """
        Full multi-bot analysis for a single coin.

        Returns the aggregated signal with per-bot breakdown.
        """
        # Normalize symbol (e.g., "BTC" -> "BTCUSDT")
        normalized = self._normalize_symbol(symbol)
        if normalized not in COINS:
            raise ValueError(f"Unsupported symbol: {symbol}. Supported: {COINS}")

        # Validate timeframe
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(TIMEFRAMES.keys())}")

        # Get aggregated signal from Brain
        aggregated: AggregatedSignal = self.brain.aggregate_signals(
            symbol=normalized,
            timeframe=timeframe,
            provider=self.provider,
        )

        # Build response matching AggregatedSignal.to_dict() + extra fields
        return {
            "symbol": normalized,
            "timeframe": timeframe,
            "final_signal": aggregated.final_signal.value,
            "confidence": round(aggregated.confidence, 2),
            "buy_score": round(aggregated.buy_score, 2),
            "sell_score": round(aggregated.sell_score, 2),
            "hold_score": round(aggregated.hold_score, 2),
            "bot_signals": [s.to_dict() for s in aggregated.bot_signals],
            "bot_probabilities": self.brain.get_bot_probabilities(
                symbol=normalized,
                timeframe=timeframe,
                provider=self.provider,
            ),
            "timestamp": aggregated.timestamp.isoformat(),
            "details": aggregated.details,
        }

    def get_indicators(
        self,
        symbol: str,
        timeframe: str = "1h",
    ) -> Dict[str, Any]:
        """Get pre-computed indicator values for a symbol/timeframe."""
        normalized = self._normalize_symbol(symbol)
        indicators = self.provider.get_indicators(normalized, timeframe)

        if indicators is None:
            raise ValueError(f"No indicator data available for {normalized}/{timeframe}")

        return {
            "symbol": normalized,
            "timeframe": timeframe,
            "indicators": indicators,
        }

    def get_market_data(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get OHLCV market data for a symbol/timeframe."""
        normalized = self._normalize_symbol(symbol)
        ohlcv = self.provider.get_ohlcv(normalized, timeframe, limit)

        if ohlcv is None:
            raise ValueError(f"No market data available for {normalized}/{timeframe}")

        opens, highs, lows, closes, volumes = ohlcv
        candles = [
            {
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v,
            }
            for o, h, l, c, v in zip(opens, highs, lows, closes, volumes)
        ]

        return {
            "symbol": normalized,
            "timeframe": timeframe,
            "limit": limit,
            "candles": candles,
        }

    def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols."""
        return COINS

    def get_supported_timeframes(self) -> Dict[str, str]:
        """Get supported timeframes with descriptions."""
        return TIMEFRAMES

    def _normalize_symbol(self, symbol: str) -> str:
        """Convert 'BTC' -> 'BTCUSDT' if needed."""
        sym = symbol.upper().strip()
        if sym.endswith("USDT"):
            return sym
        return f"{sym}USDT"


# Singleton instance for dependency injection
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """Get or create the global AnalysisService instance."""
    global _analysis_service
    if _analysis_service is None:
        from data.cache import MarketCache
        market_data = MarketData(
            cache=MarketCache(),
            ttl_sec=300,
        )
        calculator = IndicatorCalculator()
        _analysis_service = AnalysisService(market_data, calculator)
    return _analysis_service


async def init_analysis_service() -> AnalysisService:
    """Initialize the global AnalysisService (async)."""
    service = get_analysis_service()
    await service.initialize()
    return service