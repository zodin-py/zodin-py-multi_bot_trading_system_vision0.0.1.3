"""Base strategy class for all trading strategy bots (SR, SMC, Harmonic, Trend)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = __import__('logging').getLogger(__name__)


class SignalType(Enum):
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'


@dataclass
class Signal:
    bot_name: str
    signal_type: SignalType
    confidence: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'bot_name': self.bot_name,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
        }


class StrategyBot(ABC):
    """Abstract base for strategy bots in the strategies domain."""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.enabled = True
        self.last_signal: Optional[Signal] = None
        self.signal_history: List[Signal] = []
        self.max_history = 100

    @abstractmethod
    def analyze(self, symbol: str, timeframe: str, indicators) -> Signal:
        """Analyse market data and generate a Signal."""
        pass

    def calculate_probabilities(
        self, symbol: str, timeframe: str, indicators
    ) -> Tuple[float, float, float]:
        try:
            signal = self.analyze(symbol, timeframe, indicators)
            self.last_signal = signal
            self.signal_history.append(signal)
            if len(self.signal_history) > self.max_history:
                self.signal_history.pop(0)
            if signal.signal_type == SignalType.BUY:
                return signal.confidence, 0.0, 100.0 - signal.confidence
            elif signal.signal_type == SignalType.SELL:
                return 0.0, signal.confidence, 100.0 - signal.confidence
            else:
                return 0.0, 0.0, 100.0
        except Exception as e:
            logger.error(f"Error calculating probabilities for {self.name}: {e}")
            return 0.0, 0.0, 100.0

    def get_last_signal(self) -> Optional[Signal]:
        return self.last_signal

    def get_signal_history(self, limit: int = 10) -> List[Signal]:
        return self.signal_history[-limit:]

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.enabled})"
