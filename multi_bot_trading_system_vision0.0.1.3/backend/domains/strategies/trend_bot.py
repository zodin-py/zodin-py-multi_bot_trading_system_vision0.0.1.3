"""Trend Bot — MA Alignment + ADX trend analysis."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from backend.config import BOT_WEIGHTS, INDICATOR_PARAMS
from backend.domains.strategies.base import Signal, SignalType, StrategyBot

logger = logging.getLogger(__name__)


class TrendBot(StrategyBot):
    """Trend Trading Bot — Moving Averages and ADX"""

    def __init__(self):
        super().__init__(name='Trend', weight=BOT_WEIGHTS.get('trend', 0.20))
        self.adx_period = INDICATOR_PARAMS.get('adx', {}).get('period', 14)
        self.trend_threshold = INDICATOR_PARAMS.get('adx', {}).get('trend_threshold', 25)

    def analyze(self, symbol: str, timeframe: str, indicators) -> Signal:
        """Analyse trend using MA alignment and ADX values from indicators."""
        try:
            adx = getattr(indicators, 'adx', None)
            plus_di = getattr(indicators, 'plus_di', None)
            minus_di = getattr(indicators, 'minus_di', None)
            ema_9 = getattr(indicators, 'ema_9', None)
            ema_21 = getattr(indicators, 'ema_21', None)
            ema_50 = getattr(indicators, 'ema_50', None)
            ema_200 = getattr(indicators, 'ema_200', None)
            sma_20 = getattr(indicators, 'sma_20', None)
            sma_50 = getattr(indicators, 'sma_50', None)
            current_price = getattr(indicators, 'close', 0.0)

            if adx is None or plus_di is None or minus_di is None:
                return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                              confidence=0, timestamp=datetime.now(),
                              details={'error': 'Trend indicators not available'})

            if current_price == 0:
                return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                              confidence=0, timestamp=datetime.now(),
                              details={'error': 'No price data'})

            ma_values: Dict[int, float] = {
                9: ema_9 if ema_9 else current_price,
                21: ema_21 if ema_21 else current_price,
                50: ema_50 if ema_50 else current_price,
                200: ema_200 if ema_200 else current_price,
            }

            signal_type, confidence, action = self._analyze_trend(
                current_price, ma_values, adx, plus_di, minus_di
            )

            return Signal(bot_name=self.name, signal_type=signal_type,
                          confidence=round(confidence, 2), timestamp=datetime.now(),
                          details={
                              'current_price': round(current_price, 2),
                              'ema_9': round(ema_9, 2) if ema_9 else None,
                              'ema_21': round(ema_21, 2) if ema_21 else None,
                              'ema_50': round(ema_50, 2) if ema_50 else None,
                              'ema_200': round(ema_200, 2) if ema_200 else None,
                              'sma_20': round(sma_20, 2) if sma_20 else None,
                              'sma_50': round(sma_50, 2) if sma_50 else None,
                              'adx': round(adx, 2),
                              'plus_di': round(plus_di, 2),
                              'minus_di': round(minus_di, 2),
                              'trend_strength': 'Strong' if adx > self.trend_threshold else 'Weak',
                              'action': action,
                          })
        except Exception as e:
            logger.error(f"TrendBot error: {e}")
            return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                          confidence=0, timestamp=datetime.now(), details={'error': str(e)})

    def _analyze_trend(
        self, price: float, ma_values: Dict[int, float],
        adx: float, plus_di: float, minus_di: float,
    ) -> Tuple[SignalType, float, str]:
        ma9 = ma_values[9]
        ma21 = ma_values[21]
        ma50 = ma_values[50]
        ma200 = ma_values[200]

        bullish = (price > ma9 > ma21 > ma50 > ma200) or (price > ma21 > ma50 > ma200)
        bearish = (price < ma9 < ma21 < ma50 < ma200) or (price < ma21 < ma50 < ma200)
        strong = adx > self.trend_threshold

        if bullish and (strong or plus_di > minus_di):
            conf = min(100, 50 + adx)
            label = 'Strong' if strong else 'Weak'
            return SignalType.BUY, conf, f'{label} Bullish Trend (ADX: {adx:.1f})'
        elif bearish and (strong or minus_di > plus_di):
            conf = min(100, 50 + adx)
            label = 'Strong' if strong else 'Weak'
            return SignalType.SELL, conf, f'{label} Bearish Trend (ADX: {adx:.1f})'
        elif strong:
            direction = 'BUY' if plus_di > minus_di else 'SELL'
            return getattr(SignalType, direction), 40, f'Strong but unclear (ADX: {adx:.1f})'
        return SignalType.HOLD, 30, f'Range-bound (ADX: {adx:.1f})'
