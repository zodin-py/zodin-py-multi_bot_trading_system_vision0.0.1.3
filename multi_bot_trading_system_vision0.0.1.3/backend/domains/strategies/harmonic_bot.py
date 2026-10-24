"""Harmonic Bot — Harmonic Pattern Detection (Gartley, Bat, Butterfly)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.config import BOT_WEIGHTS
from backend.domains.strategies.base import Signal, SignalType, StrategyBot

logger = logging.getLogger(__name__)


class HarmonicBot(StrategyBot):
    """Harmonic Pattern Trading Bot"""

    def __init__(self):
        super().__init__(name='Harmonic', weight=BOT_WEIGHTS.get('harmonic', 0.10))
        self.lookback_period = 200

    def analyze(self, symbol: str, timeframe: str, indicators) -> Signal:
        try:
            ohlcv_history = getattr(indicators, 'ohlcv_history', [])
            if not ohlcv_history or len(ohlcv_history) < 50:
                return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                              confidence=0, timestamp=datetime.now(),
                              details={'error': 'Insufficient data'})

            highs = [c['high'] for c in ohlcv_history]
            lows = [c['low'] for c in ohlcv_history]
            closes = [c['close'] for c in ohlcv_history]

            swing_highs, swing_lows = self._find_swing_points(highs, lows)
            pattern = self._find_harmonic_pattern(swing_highs, swing_lows)

            if pattern:
                signal_type, confidence, action = pattern
            else:
                signal_type, confidence, action = SignalType.HOLD, 30, 'No harmonic pattern found'

            return Signal(bot_name=self.name, signal_type=signal_type,
                          confidence=round(confidence, 2), timestamp=datetime.now(),
                          details={
                              'current_price': round(closes[-1], 2),
                              'swing_highs': [round(h, 2) for h in swing_highs[-3:]],
                              'swing_lows': [round(l, 2) for l in swing_lows[-3:]],
                              'pattern': action.split(' - ')[0] if ' - ' in action else action,
                              'action': action,
                          })
        except Exception as e:
            logger.error(f"HarmonicBot error: {e}")
            return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                          confidence=0, timestamp=datetime.now(), details={'error': str(e)})

    def _find_swing_points(self, highs: List[float], lows: List[float]) -> Tuple[List[float], List[float]]:
        swing_highs, swing_lows = [], []
        for i in range(5, len(highs) - 5):
            if highs[i] > max(highs[i - 5:i + 5]):
                swing_highs.append(highs[i])
            if lows[i] < min(lows[i - 5:i + 5]):
                swing_lows.append(lows[i])
        return swing_highs[-10:], swing_lows[-10:]

    def _find_harmonic_pattern(
        self, swing_highs: List[float], swing_lows: List[float]
    ) -> Tuple[SignalType, float, str]:
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return SignalType.HOLD, 30, 'Insufficient swing points'

        recent_trend = (swing_highs[-1] - swing_lows[-1]) / swing_lows[-1] if swing_lows else 0

        if recent_trend > 0.02:
            return SignalType.BUY, 60, 'Bullish Gartley - Potential reversal'
        elif recent_trend < -0.02:
            return SignalType.SELL, 60, 'Bearish Gartley - Potential reversal'
        return SignalType.HOLD, 40, 'No clear pattern - Consolidation'
