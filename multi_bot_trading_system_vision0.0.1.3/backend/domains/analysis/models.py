"""Analysis domain models — AggregatedSignal, BotSignal, SignalType."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SignalType(Enum):
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'


@dataclass
class BotSignal:
    """Individual bot signal for aggregation."""
    bot_name: str
    signal_type: SignalType
    confidence: float
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'bot_name': self.bot_name,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'weight': self.weight,
            'details': self.details,
        }


@dataclass
class AggregatedSignal:
    """Aggregated signal with weighted bot breakdown."""
    final_signal: SignalType
    confidence: float
    buy_score: float
    sell_score: float
    hold_score: float
    bot_signals: List[BotSignal]
    timestamp: datetime
    symbol: str = ''
    timeframe: str = ''
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'final_signal': self.final_signal.value,
            'confidence': round(self.confidence, 2),
            'buy_score': round(self.buy_score, 2),
            'sell_score': round(self.sell_score, 2),
            'hold_score': round(self.hold_score, 2),
            'bot_signals': [s.to_dict() for s in self.bot_signals],
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'details': self.details,
        }
