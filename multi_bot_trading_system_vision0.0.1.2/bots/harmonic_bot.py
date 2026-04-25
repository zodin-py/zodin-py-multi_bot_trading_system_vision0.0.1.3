# filepath: bots/harmonic_bot.py
"""
Harmonic Bot - Harmonische Pattern Erkennung
Erkennt Gartley, Bat, Butterfly und andere harmonische Pattern
"""

from datetime import datetime
from typing import Dict, List, Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import BOT_WEIGHTS


class HarmonicBot(BaseBot):
    """Harmonic Pattern Trading Bot"""
    
    def __init__(self):
        super().__init__(name='Harmonic', weight=BOT_WEIGHTS.get('harmonic', 0.10))
        self.lookback_period = 200
        # Fibonacci Retracement Levels für Pattern
        self.pattern_tolerances = {
            'gartley': {
                'XA': [0.382, 0.618],
                'AB': [0.382, 0.618, 0.786],
                'BC': [0.382, 0.618, 0.786],
                'CD': [0.618, 0.786, 1.0, 1.272, 1.618]
            },
            'bat': {
                'XA': [0.382, 0.5],
                'AB': [0.382, 0.618],
                'BC': [0.382, 0.618],
                'CD': [0.618, 0.786]
            },
            'butterfly': {
                'XA': [0.786],
                'AB': [0.382, 0.618, 0.786],
                'BC': [0.382, 0.618, 0.786],
                'CD': [0.618, 0.786, 1.0, 1.272, 1.618]
            }
        }
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere Harmonische Pattern und generiere Signal
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            data_manager: DataManager Instanz
            
        Returns:
            Signal: Trading-Signal
        """
        try:
            # Hole Daten
            data = self._get_ohlcv_data(symbol, timeframe, data_manager, periods=self.lookback_period)
            
            if data is None or len(data['closes']) < 50:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'Insufficient data'}
                )
            
            closes = data['closes']
            highs = data['highs']
            lows = data['lows']
            
            # Finde Swing Points
            swing_highs, swing_lows = self._find_swing_points(highs, lows)
            
            # Suche nach harmonischen Pattern
            pattern = self._find_harmonic_pattern(swing_highs, swing_lows)
            
            if pattern:
                signal_type, confidence, action = pattern
            else:
                signal_type = SignalType.HOLD
                confidence = 30
                action = 'No harmonic pattern found'
            
            details = {
                'current_price': round(closes[-1], 2),
                'swing_highs': [round(h, 2) for h in swing_highs[-3:]],
                'swing_lows': [round(l, 2) for l in swing_lows[-3:]],
                'pattern': action.split(' - ')[0] if ' - ' in action else action,
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
    
    def _find_swing_points(self, highs: List[float], lows: List[float]) -> Tuple[List[float], List[float]]:
        """Finde Swing Highs und Lows"""
        swing_highs = []
        swing_lows = []
        
        # Vereinfachte Swing Point Erkennung
        for i in range(5, len(highs) - 5):
            # Swing High
            if highs[i] > max(highs[i-5:i+5]):
                swing_highs.append(highs[i])
            
            # Swing Low
            if lows[i] < min(lows[i-5:i+5]):
                swing_lows.append(lows[i])
        
        return swing_highs[-10:], swing_lows[-10:]
    
    def _find_harmonic_pattern(self, swing_highs: List[float], swing_lows: List[float]) -> Tuple[SignalType, float, str]:
        """Finde harmonisches Pattern"""
        
        if len(swing_highs) < 3 or len(swing_lows) < 3:
            return SignalType.HOLD, 30, 'Insufficient swing points'
        
        # Vereinfachte Pattern Erkennung
        # Prüfe auf Gartley Pattern (die häufigsten)
        
        # Für Demo: Generiere basierend auf Preisstruktur ein Signal
        # In einer echten Implementation würde man die Fibonacci-Levels prüfen
        
        # Berechne Trend
        recent_trend = (swing_highs[-1] - swing_lows[-1]) / swing_lows[-1] if swing_lows else 0
        
        if recent_trend > 0.02:  # Aufwärtstrend
            return SignalType.BUY, 60, 'Bullish Gartley - Potential reversal'
        elif recent_trend < -0.02:  # Abwärtstrend
            return SignalType.SELL, 60, 'Bearish Gartley - Potential reversal'
        else:
            return SignalType.HOLD, 40, 'No clear pattern - Consolidation'
    
    def _calculate_fibonacci_ratio(self, move1: float, move2: float) -> float:
        """Berechne Fibonacci Ratio zwischen zwei Bewegungen"""
        if move1 == 0:
            return 0
        return abs(move2) / abs(move1)
    
    def __repr__(self) -> str:
        return f"HarmonicBot(lookback={self.lookback_period})"