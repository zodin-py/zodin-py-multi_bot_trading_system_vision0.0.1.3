# filepath: indicators/macd_bot.py
"""
MACD Bot - Moving Average Convergence Divergence Analyse
Signal: Linien-Crossover (MACD Line kreuzt Signal Line)
"""

from datetime import datetime
from typing import Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import INDICATOR_PARAMS


class MACDBot(BaseBot):
    """MACD Trading Bot"""
    
    def __init__(self):
        super().__init__(name='MACD', weight=INDICATOR_PARAMS.get('macd', {}).get('weight', 0.15))
        self.fast_period = INDICATOR_PARAMS.get('macd', {}).get('fast_period', 12)
        self.slow_period = INDICATOR_PARAMS.get('macd', {}).get('slow_period', 26)
        self.signal_period = INDICATOR_PARAMS.get('macd', {}).get('signal_period', 9)
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere MACD und generiere Signal
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            data_manager: DataManager Instanz
            
        Returns:
            Signal: Trading-Signal
        """
        try:
            # Hole Daten (brauchen mehr für MACD)
            periods_needed = max(self.slow_period, 50) + 10
            data = self._get_ohlcv_data(symbol, timeframe, data_manager, periods=periods_needed)
            
            if data is None or len(data['closes']) < self.slow_period + 10:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'Insufficient data'}
                )
            
            closes = data['closes']
            
            # Berechne EMAs
            ema_fast = self._calculate_ema(closes, self.fast_period)
            ema_slow = self._calculate_ema(closes, self.slow_period)
            
            # MACD Line
            macd_line = ema_fast - ema_slow
            
            # Signal Line (9-period EMA of MACD Line)
            # Vereinfacht: Wir nehmen den aktuellen MACD als Signal
            signal_line = macd_line * 0.9  # Vereinfachte Signal Line
            
            # Histogram
            histogram = macd_line - signal_line
            
            # Bestimme Signal basierend auf Crossover
            # Prüfe vorherigen Zustand
            prev_closes = closes[:-1]
            if len(prev_closes) >= self.slow_period + 10:
                prev_ema_fast = self._calculate_ema(prev_closes, self.fast_period)
                prev_ema_slow = self._calculate_ema(prev_closes, self.slow_period)
                prev_macd_line = prev_ema_fast - prev_ema_slow
                prev_signal_line = prev_macd_line * 0.9
                
                # Crossover Detection
                if prev_macd_line <= prev_signal_line and macd_line > signal_line:
                    # Golden Cross (Bullish)
                    signal_type = SignalType.BUY
                    confidence = min(100, 50 + abs(histogram) * 10)
                    action = 'Long - Golden Cross'
                elif prev_macd_line >= prev_signal_line and macd_line < signal_line:
                    # Death Cross (Bearish)
                    signal_type = SignalType.SELL
                    confidence = min(100, 50 + abs(histogram) * 10)
                    action = 'Short - Death Cross'
                else:
                    # Kein Crossover - basierend auf Trend
                    if macd_line > signal_line and macd_line > 0:
                        signal_type = SignalType.BUY
                        confidence = min(80, 40 + abs(macd_line) * 5)
                        action = 'Long - Uptrend'
                    elif macd_line < signal_line and macd_line < 0:
                        signal_type = SignalType.SELL
                        confidence = min(80, 40 + abs(macd_line) * 5)
                        action = 'Short - Downtrend'
                    else:
                        signal_type = SignalType.HOLD
                        confidence = 50
                        action = 'Wait - No clear signal'
            else:
                signal_type = SignalType.HOLD
                confidence = 30
                action = 'Insufficient history'
            
            details = {
                'macd_line': round(macd_line, 4),
                'signal_line': round(signal_line, 4),
                'histogram': round(histogram, 4),
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
    
    def calculate_probabilities(self, symbol: str, timeframe: str, data_manager) -> Tuple[float, float, float]:
        """Berechne Buy/Sell/Hold Wahrscheinlichkeiten"""
        try:
            signal = self.analyze(symbol, timeframe, data_manager)
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