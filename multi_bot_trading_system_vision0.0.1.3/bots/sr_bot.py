# filepath: bots/sr_bot.py
"""
SR Bot - Support/Resistance Detection
Erkennt Support und Resistance Levels
"""

from datetime import datetime
from typing import Dict, List, Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import BOT_WEIGHTS


class SRBot(BaseBot):
    """Support/Resistance Trading Bot"""
    
    def __init__(self):
        super().__init__(name='SR', weight=BOT_WEIGHTS.get('sr', 0.15))
        self.lookback_period = 50
        self.tolerance = 0.002  # 0.2% Toleranz für Level-Erkennung
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere Support/Resistance und generiere Signal
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            data_manager: DataManager Instanz
            
        Returns:
            Signal: Trading-Signal
        """
        try:
            # Hole Daten
            data = self._get_ohlcv_data(symbol, timeframe, data_manager, periods=self.lookback_period + 20)
            
            if data is None or len(data['closes']) < self.lookback_period:
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
            
            current_price = closes[-1]
            
            # Finde Support und Resistance Levels
            support_levels = self._find_support_levels(lows, closes)
            resistance_levels = self._find_resistance_levels(highs, closes)
            
            # Analysiere Position relativ zu S/R
            signal_type, confidence, action = self._analyze_position(
                current_price, support_levels, resistance_levels
            )
            
            details = {
                'current_price': round(current_price, 2),
                'support_levels': [round(s, 2) for s in support_levels[:3]],
                'resistance_levels': [round(r, 2) for r in resistance_levels[:3]],
                'nearest_support': round(support_levels[0], 2) if support_levels else None,
                'nearest_resistance': round(resistance_levels[0], 2) if resistance_levels else None,
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
    
    def _find_support_levels(self, lows: List[float], closes: List[float]) -> List[float]:
        """Finde Support Levels"""
        supports = []
        
        for i in range(2, len(lows) - 2):
            # Lokales Tief
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                # Prüfe ob es ein signifikanter Support ist
                if lows[i] < min(closes[i-1], closes[i+1]) * 0.99:
                    supports.append(lows[i])
        
        # Sortiere und filtere
        supports = sorted(set(supports))
        
        # Gruppiere ähnliche Levels
        grouped = []
        for s in supports:
            if not grouped or abs(s - grouped[-1]) / grouped[-1] > self.tolerance:
                grouped.append(s)
            else:
                grouped[-1] = (grouped[-1] + s) / 2
        
        return sorted(grouped)[:5]
    
    def _find_resistance_levels(self, highs: List[float], closes: List[float]) -> List[float]:
        """Finde Resistance Levels"""
        resistances = []
        
        for i in range(2, len(highs) - 2):
            # Lokales Hoch
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                # Prüfe ob es ein signifikanter Resistance ist
                if highs[i] > max(closes[i-1], closes[i+1]) * 1.01:
                    resistances.append(highs[i])
        
        # Sortiere und filtere
        resistances = sorted(set(resistances), reverse=True)
        
        # Gruppiere ähnliche Levels
        grouped = []
        for r in resistances:
            if not grouped or abs(r - grouped[-1]) / grouped[-1] > self.tolerance:
                grouped.append(r)
            else:
                grouped[-1] = (grouped[-1] + r) / 2
        
        return sorted(grouped, reverse=True)[:5]
    
    def _analyze_position(self, current_price: float, supports: List[float], resistances: List[float]) -> Tuple[SignalType, float, str]:
        """Analysiere aktuelle Position relativ zu S/R"""
        
        if not supports or not resistances:
            return SignalType.HOLD, 50, 'No clear S/R levels'
        
        nearest_support = min(supports, key=lambda x: abs(x - current_price))
        nearest_resistance = min(resistances, key=lambda x: abs(x - current_price))
        
        # Berechne Distanzen
        dist_to_support = (current_price - nearest_support) / nearest_support
        dist_to_resistance = (nearest_resistance - current_price) / nearest_resistance
        
        # Stärke des Levels (näher = stärker)
        support_strength = 1 - (dist_to_support / max(dist_to_support, dist_to_resistance))
        resistance_strength = 1 - (dist_to_resistance / max(dist_to_support, dist_to_resistance))
        
        if dist_to_support < 0.01:  # Innerhalb 1% zum Support
            # Nah an Support -> Buy
            confidence = min(100, 50 + support_strength * 50)
            return SignalType.BUY, confidence, f'Near Support at {nearest_support}'
        
        elif dist_to_resistance < 0.01:  # Innerhalb 1% zum Resistance
            # Nah an Resistance -> Sell
            confidence = min(100, 50 + resistance_strength * 50)
            return SignalType.SELL, confidence, f'Near Resistance at {nearest_resistance}'
        
        elif dist_to_support < dist_to_resistance:
            # Näher an Support
            return SignalType.BUY, 40, f'Closer to Support ({nearest_support})'
        
        else:
            # Näher an Resistance
            return SignalType.SELL, 40, f'Closer to Resistance ({nearest_resistance})'
    
    def __repr__(self) -> str:
        return f"SRBot(lookback={self.lookback_period}, tolerance={self.tolerance})"