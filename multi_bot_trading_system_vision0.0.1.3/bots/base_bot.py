# filepath: bots/base_bot.py
"""
Base Bot - Abstrakte Basisklasse für alle Trading-Bots
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging


logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Signal-Typen"""
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'


@dataclass
class Signal:
    """Trading Signal"""
    bot_name: str
    signal_type: SignalType
    confidence: float  # 0-100
    timestamp: datetime
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> dict:
        return {
            'bot_name': self.bot_name,
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }


class BaseBot(ABC):
    """Abstrakte Basisklasse für alle Trading-Bots"""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.enabled = True
        self.last_signal: Optional[Signal] = None
        self.signal_history: List[Signal] = []
        self.max_history = 100

    @abstractmethod
    def analyze(self, symbol: str, timeframe: str, provider) -> Signal:
        """
        Analysiere Marktdaten und generiere ein Signal

        Args:
            symbol: Trading-Paar (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '1m', '5m', '1h')
            provider: IndicatorProvider Instanz für Marktdaten und Indikatoren

        Returns:
            Signal: Trading-Signal mit Konfidenz
        """
        pass

    def calculate_probabilities(self, symbol: str, timeframe: str, provider) -> Tuple[float, float, float]:
        """
        Berechne Buy/Sell/Hold Wahrscheinlichkeiten

        Returns:
            Tuple[buy_prob, sell_prob, hold_prob]
        """
        try:
            signal = self.analyze(symbol, timeframe, provider)
            self.last_signal = signal

            # Speichere in History
            self.signal_history.append(signal)
            if len(self.signal_history) > self.max_history:
                self.signal_history.pop(0)

            if signal.signal_type == SignalType.BUY:
                return signal.confidence, 0, 100 - signal.confidence
            elif signal.signal_type == SignalType.SELL:
                return 0, signal.confidence, 100 - signal.confidence
            else:
                return 0, 0, 100

        except Exception as e:
            logger.error(f"Error calculating probabilities for {self.name}: {e}")
            return 0, 0, 100

    def get_last_signal(self) -> Optional[Signal]:
        """Hole das letzte Signal"""
        return self.last_signal

    def get_signal_history(self, limit: int = 10) -> List[Signal]:
        """Hole Signal-History"""
        return self.signal_history[-limit:]

    def enable(self):
        """Aktiviere den Bot"""
        self.enabled = True
        logger.info(f"Bot {self.name} enabled")

    def disable(self):
        """Deaktiviere den Bot"""
        self.enabled = False
        logger.info(f"Bot {self.name} disabled")

    def is_enabled(self) -> bool:
        """Prüfe ob Bot aktiviert ist"""
        return self.enabled

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Hole Indikatorwerte aus dem Provider."""
        return None

    def get_ohlcv(self, symbol: str, timeframe: str, periods: int = 50) -> Optional[Tuple[List[float], ...]]:
        """Hole OHLCV Daten aus dem Provider."""
        return None

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        """Prüfe ob Daten veraltet sind."""
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.enabled})"
