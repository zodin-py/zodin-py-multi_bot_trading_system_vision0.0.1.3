"""SMC Bot — Smart Money Concepts (Order Blocks & Fair Value Gaps)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.config import BOT_WEIGHTS
from backend.domains.strategies.base import Signal, SignalType, StrategyBot

logger = logging.getLogger(__name__)


class SMCBot(StrategyBot):
    """Smart Money Concepts Trading Bot"""

    def __init__(self):
        super().__init__(name='SMC', weight=BOT_WEIGHTS.get('smc', 0.15))
        self.lookback_period = 100
        self.fvg_threshold = 0.5  # % für FVG Erkennung

    def analyze(self, symbol: str, timeframe: str, indicators) -> Signal:
        try:
            ohlcv_history = getattr(indicators, 'ohlcv_history', [])
            if not ohlcv_history or len(ohlcv_history) < 20:
                return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                              confidence=0, timestamp=datetime.now(),
                              details={'error': 'Insufficient data'})

            closes = [c['close'] for c in ohlcv_history]
            highs = [c['high'] for c in ohlcv_history]
            lows = [c['low'] for c in ohlcv_history]
            volumes = [c.get('volume', 1.0) for c in ohlcv_history]

            buy_ob, sell_ob = self._find_orderblocks(closes, highs, lows, volumes)
            bullish_fvg, bearish_fvg = self._find_fvgs(highs, lows, closes)
            signal_type, confidence, action = self._analyze_smc(
                closes[-1], buy_ob, sell_ob, bullish_fvg, bearish_fvg
            )

            return Signal(bot_name=self.name, signal_type=signal_type,
                          confidence=round(confidence, 2), timestamp=datetime.now(),
                          details={
                              'current_price': round(closes[-1], 2),
                              'buy_orderblocks': [round(ob, 2) for ob in buy_ob[:3]],
                              'sell_orderblocks': [round(ob, 2) for ob in sell_ob[:3]],
                              'bullish_fvg': bullish_fvg,
                              'bearish_fvg': bearish_fvg,
                              'action': action,
                          })
        except Exception as e:
            logger.error(f"SMCBot error: {e}")
            return Signal(bot_name=self.name, signal_type=SignalType.HOLD,
                          confidence=0, timestamp=datetime.now(),
                          details={'error': str(e)})

    def _find_orderblocks(
        self, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]
    ) -> Tuple[List[float], List[float]]:
        buy_obs: List[float] = []
        sell_obs: List[float] = []
        for i in range(2, len(closes) - 2):
            avg_vol = sum(volumes[max(0, i - 5):i]) / 5 if all(v > 0 for v in volumes[max(0, i - 5):i]) else 1.0
            if closes[i] > closes[i - 2] and closes[i + 1] < closes[i]:
                if volumes[i] > avg_vol and lows[i] < min(closes[i - 2:i]):
                    buy_obs.append(lows[i])
            if closes[i] < closes[i - 2] and closes[i + 1] > closes[i]:
                if volumes[i] > avg_vol and highs[i] > max(closes[i - 2:i]):
                    sell_obs.append(highs[i])
        return buy_obs[-5:], sell_obs[-5:]

    def _find_fvgs(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[bool, bool]:
        bullish_fvg, bearish_fvg = False, False
        for i in range(2, len(closes) - 2):
            gap_up = highs[i] - lows[i - 2]
            if (gap_up > 0 and gap_up / closes[i - 2] > self.fvg_threshold / 100
                    and closes[i + 1] < closes[i]):
                bullish_fvg = True
            gap_down = highs[i - 2] - lows[i]
            if (gap_down > 0 and gap_down / closes[i - 2] > self.fvg_threshold / 100
                    and closes[i + 1] > closes[i]):
                bearish_fvg = True
        return bullish_fvg, bearish_fvg

    def _analyze_smc(
        self, price: float, buy_ob: List[float], sell_ob: List[float],
        bullish_fvg: bool, bearish_fvg: bool,
    ) -> Tuple[SignalType, float, str]:
        buy_score, sell_score = 0.0, 0.0
        for ob in buy_ob:
            if price > ob and (price - ob) / ob < 0.02:
                buy_score += 30
        for ob in sell_ob:
            if price < ob and (ob - price) / ob < 0.02:
                sell_score += 30
        if bullish_fvg:
            buy_score += 25
        if bearish_fvg:
            sell_score += 25
        if buy_score > sell_score and buy_score > 30:
            return SignalType.BUY, min(100, buy_score), f'Bullish SMC (Score: {buy_score:.0f})'
        elif sell_score > buy_score and sell_score > 30:
            return SignalType.SELL, min(100, sell_score), f'Bearish SMC (Score: {sell_score:.0f})'
        return SignalType.HOLD, 50, 'No clear SMC signal'
