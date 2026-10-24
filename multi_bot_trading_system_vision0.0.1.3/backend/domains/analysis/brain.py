"""Analysis domain brain — Signal aggregation from all bots."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.config import BOT_WEIGHTS, SIGNAL_THRESHOLDS
from backend.domains.analysis.models import AggregatedSignal, BotSignal, SignalType
from backend.domains.strategies.base import Signal as BotSignalBase

logger = logging.getLogger(__name__)


class Brain:
    """Aggregates signals from all trading bots into a final decision."""

    def __init__(
        self,
        min_buy_prob: float = SIGNAL_THRESHOLDS.get('min_buy_probability', 65),
        min_sell_prob: float = SIGNAL_THRESHOLDS.get('min_sell_probability', 65),
        min_confidence: float = SIGNAL_THRESHOLDS.get('min_confidence', 60),
    ):
        self.min_buy_prob = min_buy_prob
        self.min_sell_prob = min_sell_prob
        self.min_confidence = min_confidence
        self.bot_weights = BOT_WEIGHTS.copy()
        self.last_aggregated: Optional[AggregatedSignal] = None
        self.signal_history: List[AggregatedSignal] = []
        self.max_history = 100

    def aggregate_signals(
        self,
        symbol: str,
        timeframe: str,
        bot_signals: List[BotSignalBase],
    ) -> AggregatedSignal:
        """Aggregate individual bot signals into a final weighted signal."""
        try:
            buy_score = sell_score = hold_score = 0.0
            total_weight = 0.0
            aggregated_bots: List[BotSignal] = []

            for signal in bot_signals:
                weight = self._get_bot_weight(signal.bot_name)
                total_weight += weight
                aggregated_bots.append(BotSignal(
                    bot_name=signal.bot_name,
                    signal_type=self._map_signal_type(signal.signal_type),
                    confidence=signal.confidence,
                    weight=weight,
                    details=signal.details,
                ))

                if signal.signal_type == SignalType.BUY:
                    buy_score += signal.confidence * weight
                elif signal.signal_type == SignalType.SELL:
                    sell_score += signal.confidence * weight
                else:
                    hold_score += (100 - signal.confidence) * weight

            # Normalize scores
            if total_weight > 0:
                buy_score /= total_weight
                sell_score /= total_weight
                hold_score /= total_weight

            final_signal, confidence = self._determine_final(
                buy_score, sell_score, hold_score
            )

            aggregated = AggregatedSignal(
                final_signal=final_signal,
                confidence=round(confidence, 2),
                buy_score=round(buy_score, 2),
                sell_score=round(sell_score, 2),
                hold_score=round(hold_score, 2),
                bot_signals=aggregated_bots,
                timestamp=datetime.now(),
                symbol=symbol,
                timeframe=timeframe,
                details={
                    'active_bots': len(bot_signals),
                    'min_buy_threshold': self.min_buy_prob,
                    'min_sell_threshold': self.min_sell_prob,
                },
            )

            self.last_aggregated = aggregated
            self.signal_history.append(aggregated)
            if len(self.signal_history) > self.max_history:
                self.signal_history.pop(0)

            return aggregated

        except Exception as e:
            logger.error(f"Brain aggregation error: {e}")
            return AggregatedSignal(
                final_signal=SignalType.HOLD,
                confidence=0,
                buy_score=0,
                sell_score=0,
                hold_score=100,
                bot_signals=[],
                timestamp=datetime.now(),
                symbol=symbol,
                timeframe=timeframe,
                details={'error': str(e)},
            )

    def _map_signal_type(self, sig_type) -> SignalType:
        """Map SignalType from any source to our domain SignalType."""
        if hasattr(sig_type, 'value'):
            val = sig_type.value
        else:
            val = str(sig_type).lower()
        mapping = {'buy': SignalType.BUY, 'sell': SignalType.SELL, 'hold': SignalType.HOLD}
        return mapping.get(val, SignalType.HOLD)

    def _get_bot_weight(self, bot_name: str) -> float:
        name_lower = bot_name.lower()
        for key, weight in self.bot_weights.items():
            if key in name_lower or name_lower in key:
                return weight
        return 1.0

    def _determine_final(
        self, buy: float, sell: float, hold: float
    ) -> Tuple[SignalType, float]:
        total = buy + sell + hold
        if total > 0:
            buy_pct = (buy / total) * 100
            sell_pct = (sell / total) * 100
            hold_pct = (hold / total) * 100
        else:
            buy_pct = sell_pct = hold_pct = 0

        if buy_pct >= self.min_buy_prob and buy_pct > sell_pct:
            return SignalType.BUY, min(100, buy_pct)
        elif sell_pct >= self.min_sell_prob and sell_pct > buy_pct:
            return SignalType.SELL, min(100, sell_pct)
        else:
            return SignalType.HOLD, max(hold_pct, 50)

    def get_bot_probabilities(
        self, bot_signals: List[BotSignalBase]
    ) -> Dict[str, Dict[str, float]]:
        """Get per-bot buy/sell/hold probabilities."""
        probs: Dict[str, Dict[str, float]] = {}
        for sig in bot_signals:
            if sig.signal_type.value == 'buy':
                probs[sig.bot_name] = {
                    'buy': sig.confidence,
                    'sell': 0.0,
                    'hold': 100.0 - sig.confidence,
                }
            elif sig.signal_type.value == 'sell':
                probs[sig.bot_name] = {
                    'buy': 0.0,
                    'sell': sig.confidence,
                    'hold': 100.0 - sig.confidence,
                }
            else:
                probs[sig.bot_name] = {
                    'buy': 0.0,
                    'sell': 0.0,
                    'hold': 100.0,
                }
        return probs

    def get_last_signal(self) -> Optional[AggregatedSignal]:
        return self.last_aggregated

    def get_signal_history(self, limit: int = 10) -> List[AggregatedSignal]:
        return self.signal_history[-limit:]

    def __repr__(self) -> str:
        return f"Brain(min_buy={self.min_buy_prob}, min_sell={self.min_sell_prob})"
