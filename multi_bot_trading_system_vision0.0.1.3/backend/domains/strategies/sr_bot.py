"""SR Bot — Support / Resistance Detection."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.config import BOT_WEIGHTS
from backend.domains.strategies.base import Signal, SignalType, StrategyBot

logger = logging.getLogger(__name__)


class SRBot(StrategyBot):
    """Support/Resistance Trading Bot"""

    def __init__(self):
        super().__init__(name='SR', weight=BOT_WEIGHTS.get('sr', 0.15))
        self.lookback_period = 50
        self.tolerance = 0.002  # 0.2% Toleranz für Level-Erkennung

    def analyze(self, symbol: str, timeframe: str, indicators) -> Signal:
        """Analyse S/R levels from historical OHLCV candles."""
        try:
            ohlcv_history = getattr(indicators, 'ohlcv_history', [])
            if not ohlcv_history or len(ohlcv_history) < self.lookback_period:
                return Signal(
                    bot_name=self.name, signal_type=SignalType.HOLD,
                    confidence=0, timestamp=datetime.now(),
                    details={'error': 'Insufficient OHLCV data'},
                )

            closes = [c['close'] for c in ohlcv_history]
            highs = [c['high'] for c in ohlcv_history]
            lows = [c['low'] for c in ohlcv_history]
            current_price = closes[-1]

            support_levels = self._find_support_levels(lows, closes)
            resistance_levels = self._find_resistance_levels(highs, closes)

            signal_type, confidence, action = self._analyze_position(
                current_price, support_levels, resistance_levels
            )

            return Signal(
                bot_name=self.name, signal_type=signal_type,
                confidence=round(confidence, 2), timestamp=datetime.now(),
                details={
                    'current_price': round(current_price, 2),
                    'support_levels': [round(s, 2) for s in support_levels[:3]],
                    'resistance_levels': [round(r, 2) for r in resistance_levels[:3]],
                    'nearest_support': round(support_levels[0], 2) if support_levels else None,
                    'nearest_resistance': round(resistance_levels[0], 2) if resistance_levels else None,
                    'action': action,
                },
            )
        except Exception as e:
            logger.error(f"SRBot error: {e}")
            return Signal(
                bot_name=self.name, signal_type=SignalType.HOLD,
                confidence=0, timestamp=datetime.now(), details={'error': str(e)},
            )

    def _find_support_levels(self, lows: List[float], closes: List[float]) -> List[float]:
        supports = []
        for i in range(2, len(lows) - 2):
            if (lows[i] < lows[i - 1] and lows[i] < lows[i - 2]
                    and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]):
                if lows[i] < min(closes[i - 1], closes[i + 1]) * 0.99:
                    supports.append(lows[i])
        supports = sorted(set(supports))
        grouped: List[float] = []
        for s in supports:
            if not grouped or abs(s - grouped[-1]) / grouped[-1] > self.tolerance:
                grouped.append(s)
            else:
                grouped[-1] = (grouped[-1] + s) / 2
        return sorted(grouped)[:5]

    def _find_resistance_levels(self, highs: List[float], closes: List[float]) -> List[float]:
        resistances = []
        for i in range(2, len(highs) - 2):
            if (highs[i] > highs[i - 1] and highs[i] > highs[i - 2]
                    and highs[i] > highs[i + 1] and highs[i] > highs[i + 2]):
                if highs[i] > max(closes[i - 1], closes[i + 1]) * 1.01:
                    resistances.append(highs[i])
        resistances = sorted(set(resistances), reverse=True)
        grouped: List[float] = []
        for r in resistances:
            if not grouped or abs(r - grouped[-1]) / grouped[-1] > self.tolerance:
                grouped.append(r)
            else:
                grouped[-1] = (grouped[-1] + r) / 2
        return sorted(grouped, reverse=True)[:5]

    def _analyze_position(
        self, price: float, supports: List[float], resistances: List[float]
    ) -> Tuple[SignalType, float, str]:
        if not supports or not resistances:
            return SignalType.HOLD, 50.0, 'No clear S/R levels'

        nearest_support = min(supports, key=lambda x: abs(x - price))
        nearest_resistance = min(resistances, key=lambda x: abs(x - price))

        dist_support = (price - nearest_support) / nearest_support
        dist_resistance = (nearest_resistance - price) / nearest_resistance
        max_dist = max(dist_support, dist_resistance)
        support_strength = 1 - (dist_support / max_dist) if max_dist else 0
        resistance_strength = 1 - (dist_resistance / max_dist) if max_dist else 0

        if dist_support < 0.01:
            conf = min(100, 50 + support_strength * 50)
            return SignalType.BUY, conf, f'Near Support at {nearest_support:.2f}'
        elif dist_resistance < 0.01:
            conf = min(100, 50 + resistance_strength * 50)
            return SignalType.SELL, conf, f'Near Resistance at {nearest_resistance:.2f}'
        elif dist_support < dist_resistance:
            return SignalType.BUY, 40, f'Closer to Support ({nearest_support:.2f})'
        else:
            return SignalType.SELL, 40, f'Closer to Resistance ({nearest_resistance:.2f})'
