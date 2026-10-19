# filepath: indicators/macd_bot.py
"""
MACD Bot - Moving Average Convergence Divergence Analyse
Signal: Linien-Crossover (MACD Line kreuzt Signal Line)

Liest vorberechnete Indikatoren aus dem IndicatorProvider.
"""

from datetime import datetime
from typing import Tuple, Optional

from bots.base_bot import BaseBot, Signal, SignalType
from config import INDICATOR_PARAMS
from indicators.provider import IndicatorProvider


class MACDBot(BaseBot):
    """MACD Trading Bot"""

    def __init__(self, provider: Optional[IndicatorProvider] = None):
        super().__init__(name='MACD', weight=INDICATOR_PARAMS.get('macd', {}).get('weight', 0.15))
        self.fast_period = INDICATOR_PARAMS.get('macd', {}).get('fast_period', 12)
        self.slow_period = INDICATOR_PARAMS.get('macd', {}).get('slow_period', 26)
        self.signal_period = INDICATOR_PARAMS.get('macd', {}).get('signal_period', 9)
        self._provider = provider

    @property
    def provider(self) -> Optional[IndicatorProvider]:
        return self._provider

    @provider.setter
    def provider(self, provider: IndicatorProvider):
        self._provider = provider

    def analyze(self, symbol: str, timeframe: str, provider: IndicatorProvider) -> Signal:
        """
        Analysiere MACD und generiere Signal

        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            provider: IndicatorProvider Instanz für Marktdaten und Indikatoren

        Returns:
            Signal: Trading-Signal
        """
        try:
            # Hole Indikatoren vom Provider
            indicators = provider.get_indicators(symbol, timeframe)

            if indicators is None:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'No indicator data available'}
                )

            macd = indicators.get('macd')
            macd_signal = indicators.get('macd_signal')
            macd_hist = indicators.get('macd_hist')

            if macd is None or macd_signal is None:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'MACD not available'}
                )

            # Prüfe auf veraltete Daten
            if provider.is_stale(symbol, timeframe):
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'Stale data', 'macd': round(macd, 4)}
                )

            # Bestimme Signal basierend auf Crossover und Trend
            if macd > macd_signal and macd > 0:
                # MACD über Signal Line und positiv -> Bullish
                signal_type = SignalType.BUY
                confidence = min(100, 60 + abs(macd_hist) * 10)
                action = 'Long - MACD bullish'
            elif macd < macd_signal and macd < 0:
                # MACD unter Signal Line und negativ -> Bearish
                signal_type = SignalType.SELL
                confidence = min(100, 60 + abs(macd_hist) * 10)
                action = 'Short - MACD bearish'
            elif macd > macd_signal:
                # MACD über Signal Line aber noch negativ -> Potential Buy
                signal_type = SignalType.BUY
                confidence = min(70, 40 + abs(macd_hist) * 5)
                action = 'Long - MACD turning up'
            elif macd < macd_signal:
                # MACD unter Signal Line aber noch positiv -> Potential Sell
                signal_type = SignalType.SELL
                confidence = min(70, 40 + abs(macd_hist) * 5)
                action = 'Short - MACD turning down'
            else:
                signal_type = SignalType.HOLD
                confidence = 50
                action = 'Wait - No clear signal'

            details = {
                'macd_line': round(macd, 4),
                'signal_line': round(macd_signal, 4),
                'histogram': round(macd_hist, 4),
                'action': action
            }

            return Signal(
                bot_name=self.name,
                signal_type=signal_type,
                confidence=round(confidence, 2),
                timestamp=datetime.now(),
                details=details
            )

        except Exception as e:
            return Signal(
                bot_name=self.name,
                signal_type=SignalType.HOLD,
                confidence=0,
                timestamp=datetime.now(),
                details={'error': str(e)}
            )

    def calculate_probabilities(self, symbol: str, timeframe: str, provider: IndicatorProvider) -> Tuple[float, float, float]:
        """Berechne Buy/Sell/Hold Wahrscheinlichkeiten"""
        try:
            signal = self.analyze(symbol, timeframe, provider)
            self.last_signal = signal

            if signal.signal_type == SignalType.BUY:
                return signal.confidence, 10, 100 - signal.confidence - 10
            elif signal.signal_type == SignalType.SELL:
                return 10, signal.confidence, 100 - signal.confidence - 10
            else:
                return 15, 15, 70

        except Exception as e:
            return 0, 0, 100

    def __repr__(self) -> str:
        return f"MACDBot(fast={self.fast_period}, slow={self.slow_period}, signal={self.signal_period})"