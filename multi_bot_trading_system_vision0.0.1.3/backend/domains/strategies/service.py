"""Strategies domain service — orchestrates all strategy bots."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.config import BOT_WEIGHTS
from backend.domains.strategies.base import Signal, SignalType, StrategyBot
from backend.domains.strategies.sr_bot import SRBot
from backend.domains.strategies.smc_bot import SMCBot
from backend.domains.strategies.harmonic_bot import HarmonicBot
from backend.domains.strategies.trend_bot import TrendBot

logger = logging.getLogger(__name__)


class StrategiesService:
    """Manages all strategy bots and aggregates their signals."""

    def __init__(self):
        self.bots: List[StrategyBot] = [
            SRBot(),
            SMCBot(),
            HarmonicBot(),
            TrendBot(),
        ]

    def analyze_all(self, symbol: str, timeframe: str, indicators) -> Dict[str, Any]:
        """Run all strategy bots and return combined weighted results."""
        bot_signals = []
        for bot in self.bots:
            if not bot.is_enabled():
                continue
            try:
                signal = bot.analyze(symbol, timeframe, indicators)
                bot_signals.append(signal.to_dict())
            except Exception as e:
                logger.warning(f"Strategy bot {bot.name} failed: {e}")
                bot_signals.append({
                    'bot_name': bot.name,
                    'signal_type': SignalType.HOLD.value,
                    'confidence': 0,
                    'details': {'error': str(e)},
                })

        total_weight = sum(b.weight for b in self.bots if b.is_enabled())
        buy_weight, sell_weight, hold_weight = 0.0, 0.0, 0.0
        for bot, sig in zip(self.bots, bot_signals):
            w = bot.weight / total_weight if total_weight > 0 else 0
            if sig['signal_type'] == 'buy':
                buy_weight += sig['confidence'] / 100 * w
            elif sig['signal_type'] == 'sell':
                sell_weight += sig['confidence'] / 100 * w
            else:
                hold_weight += (100 - sig['confidence']) / 100 * w

        final_signal = ('buy' if buy_weight > sell_weight and buy_weight > 0.3
                        else 'sell' if sell_weight > buy_weight and sell_weight > 0.3
                        else 'hold')
        confidence = max(buy_weight, sell_weight) * 100

        return {
            'final_signal': final_signal,
            'confidence': round(confidence, 2),
            'bot_signals': bot_signals,
            'buy_weight': round(buy_weight, 4),
            'sell_weight': round(sell_weight, 4),
            'hold_weight': round(hold_weight, 4),
        }

    def get_bot_probabilities(
        self, symbol: str, timeframe: str, indicators
    ) -> Dict[str, Dict[str, float]]:
        """Get per-bot buy/sell/hold probabilities."""
        probs: Dict[str, Dict[str, float]] = {}
        for bot in self.bots:
            buy, sell, hold = bot.calculate_probabilities(symbol, timeframe, indicators)
            probs[bot.name] = {'buy': round(buy, 2), 'sell': round(sell, 2), 'hold': round(hold, 2)}
        return probs

    @property
    def bot_names(self) -> List[str]:
        return [b.name for b in self.bots]
