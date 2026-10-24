"""Analysis domain service — orchestrates indicators, strategies, and brain aggregation."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.config import COINS, TIMEFRAMES
from backend.domains.analysis.brain import Brain
from backend.domains.analysis.models import AggregatedSignal
from backend.domains.indicators.models import IndicatorValues
from backend.domains.indicators.service import IndicatorService
from backend.domains.strategies.service import StrategiesService

logger = logging.getLogger(__name__)


class AnalysisService:
    """Central analysis service coordinating indicators, strategies, and signal aggregation."""

    def __init__(
        self,
        indicator_service: Optional[IndicatorService] = None,
        strategies_service: Optional[StrategiesService] = None,
        brain: Optional[Brain] = None,
    ):
        self.indicator_service = indicator_service or IndicatorService()
        self.strategies_service = strategies_service or StrategiesService()
        self.brain = brain or Brain()

    async def initialize(self) -> None:
        """Initialize async components (indicator provider)."""
        logger.info("AnalysisService initialized")

    async def shutdown(self) -> None:
        """Cleanup async components."""
        logger.info("AnalysisService shutdown complete")

    async def analyze_coin(
        self,
        symbol: str,
        timeframe: str = '1h',
    ) -> Dict[str, Any]:
        """Full multi-bot analysis for a single coin.

        Returns aggregated signal with per-bot breakdown.
        """
        try:
            # Step 1: Fetch indicators
            indicators: Optional[IndicatorValues] = await self.indicator_service.get_indicators(
                symbol, timeframe
            )
            if indicators is None:
                return {
                    'error': f'No indicator data for {symbol}/{timeframe}',
                    'symbol': symbol,
                    'timeframe': timeframe,
                }

            # Step 2: Run strategy bots
            strategy_result = self.strategies_service.analyze_all(symbol, timeframe, indicators)

            # Step 3: Aggregate via Brain
            bot_signals = []
            for bot in self.strategies_service.bots:
                sig = bot.last_signal
                if sig:
                    bot_signals.append(sig)

            aggregated = self.brain.aggregate_signals(symbol, timeframe, bot_signals)

            # Combine results
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators.to_dict(),
                'strategy_result': strategy_result,
                'aggregated_signal': aggregated.to_dict(),
            }

        except Exception as e:
            logger.error(f"Error analyzing {symbol}/{timeframe}: {e}")
            return {
                'error': str(e),
                'symbol': symbol,
                'timeframe': timeframe,
            }

    async def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get raw indicator values for a symbol/timeframe."""
        indicators = await self.indicator_service.get_indicators(symbol, timeframe)
        return indicators.to_dict() if indicators else None

    async def get_market_data(
        self, symbol: str, timeframe: str = '1h', limit: int = 50
    ) -> Dict[str, Any]:
        """Get market data including recent OHLCV candles."""
        indicators = await self.indicator_service.get_indicators(symbol, timeframe)
        if indicators is None:
            return {'error': 'No data available'}
        result = indicators.to_dict()
        result['ohlcv_history'] = getattr(indicators, 'ohlcv_history', [])
        return result

    async def analyze_all_coins(
        self, symbols: Optional[List[str]] = None, timeframe: str = '1h'
    ) -> Dict[str, Any]:
        """Analyze all configured coins (or provided list)."""
        coins = symbols or COINS
        results = {}
        for symbol in coins:
            try:
                results[symbol] = await self.analyze_coin(symbol, timeframe)
            except Exception as e:
                logger.warning(f"Failed to analyze {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        return results

    def get_bot_probabilities(
        self, symbol: str, timeframe: str, indicators: IndicatorValues
    ) -> Dict[str, Dict[str, float]]:
        """Get per-bot buy/sell/hold probabilities."""
        return self.strategies_service.get_bot_probabilities(symbol, timeframe, indicators)
