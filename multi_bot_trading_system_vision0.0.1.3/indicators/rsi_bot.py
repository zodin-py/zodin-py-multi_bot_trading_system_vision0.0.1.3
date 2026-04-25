# filepath: indicators/rsi_bot.py
"""
RSI Bot - Relative Strength Index Analyse
Buy wenn RSI < 30 (oversold), Sell wenn RSI > 70 (overbought)
"""

from datetime import datetime
from typing import Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import INDICATOR_PARAMS


class RSIBot(BaseBot):
    """RSI Trading Bot"""
    
    def __init__(self):
        super().__init__(name='RSI', weight=INDICATOR_PARAMS.get('rsi', {}).get('weight', 0.15))
        self.period = INDICATOR_PARAMS.get('rsi', {}).get('period', 14)
        self.overbought = INDICATOR_PARAMS.get('rsi', {}).get('overbought', 70)
        self.oversold = INDICATOR_PARAMS.get('rsi', {}).get('oversold', 30)
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere RSI und generiere Signal
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            data_manager: DataManager Instanz
            
        Returns:
            Signal: Trading-Signal
        """
        try:
            # Hole Daten
            data = self._get_ohlcv_data(symbol, timeframe, data_manager, periods=self.period + 10)
            
            if data is None or len(data['closes']) < self.period + 1:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'Insufficient data'}
                )
            
            # Berechne RSI
            rsi = self._calculate_rsi(data['closes'], self.period)
            
            # Bestimme Signal basierend auf RSI
            if rsi < self.oversold:
                # Oversold -> Buy Signal
                # Je tiefer der RSI, desto stärker das Buy Signal
                confidence = min(100, (self.oversold - rsi) / (self.oversold - 10) * 100)
                signal_type = SignalType.BUY
                details = {
                    'rsi': round(rsi, 2),
                    'zone': 'oversold',
                    'action': 'Long'
                }
            elif rsi > self.overbought:
                # Overbought -> Sell Signal
                confidence = min(100, (rsi - self.overbought) / (90 - self.overbought) * 100)
                signal_type = SignalType.SELL
                details = {
                    'rsi': round(rsi, 2),
                    'zone': 'overbought',
                    'action': 'Short'
                }
            else:
                # Neutraler Bereich -> Hold
                # Berechne Konfidenz basierend auf Entfernung von Extremen
                if rsi > 50:
                    # Leichte Tendenz nach unten
                    distance_from_top = self.overbought - rsi
                    confidence = (distance_from_top / (self.overbought - 50)) * 50
                else:
                    # Leichte Tendenz nach oben
                    distance_from_bottom = rsi - self.oversold
                    confidence = (distance_from_bottom / (50 - self.oversold)) * 50
                
                signal_type = SignalType.HOLD
                details = {
                    'rsi': round(rsi, 2),
                    'zone': 'neutral',
                    'action': 'Wait'
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
                return signal.confidence, 5, 100 - signal.confidence - 5
            elif signal.signal_type == SignalType.SELL:
                return 5, signal.confidence, 100 - signal.confidence - 5
            else:
                return 10, 10, 80
                
        except Exception as e:
            return 0, 0, 100
    
    def __repr__(self) -> str:
        return f"RSIBot(period={self.period}, oversold={self.oversold}, overbought={self.overbought})"