# filepath: indicators/mfi_bot.py
"""
MFI Bot - Money Flow Index Analyse
Buy wenn MFI < 20 (oversold), Sell wenn MFI > 80 (overbought)
Kombiniert Preis und Volumen
"""

from datetime import datetime
from typing import Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import INDICATOR_PARAMS


class MFIBot(BaseBot):
    """MFI (Money Flow Index) Trading Bot"""
    
    def __init__(self):
        super().__init__(name='MFI', weight=INDICATOR_PARAMS.get('mfi', {}).get('weight', 0.10))
        self.period = INDICATOR_PARAMS.get('mfi', {}).get('period', 14)
        self.overbought = INDICATOR_PARAMS.get('mfi', {}).get('overbought', 80)
        self.oversold = INDICATOR_PARAMS.get('mfi', {}).get('oversold', 20)
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere MFI und generiere Signal
        
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
            
            # Berechne MFI
            mfi = self._calculate_mfi(
                data['highs'],
                data['lows'],
                data['closes'],
                data['volumes'],
                self.period
            )
            
            # Bestimme Signal basierend auf MFI
            if mfi < self.oversold:
                # Oversold -> Buy Signal (Volumen bestätigt)
                confidence = min(100, (self.oversold - mfi) / (self.oversold - 10) * 100)
                signal_type = SignalType.BUY
                details = {
                    'mfi': round(mfi, 2),
                    'zone': 'oversold',
                    'action': 'Long - Money flowing in'
                }
            elif mfi > self.overbought:
                # Overbought -> Sell Signal
                confidence = min(100, (mfi - self.overbought) / (90 - self.overbought) * 100)
                signal_type = SignalType.SELL
                details = {
                    'mfi': round(mfi, 2),
                    'zone': 'overbought',
                    'action': 'Short - Money flowing out'
                }
            else:
                # Neutraler Bereich -> Hold
                if mfi > 50:
                    distance_from_top = self.overbought - mfi
                    confidence = (distance_from_top / (self.overbought - 50)) * 50
                else:
                    distance_from_bottom = mfi - self.oversold
                    confidence = (distance_from_bottom / (50 - self.oversold)) * 50
                
                signal_type = SignalType.HOLD
                details = {
                    'mfi': round(mfi, 2),
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
        return f"MFIBot(period={self.period}, oversold={self.oversold}, overbought={self.overbought})"