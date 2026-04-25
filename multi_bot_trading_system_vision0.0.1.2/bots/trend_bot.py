# filepath: bots/trend_bot.py
"""
Trend Bot - Trendanalyse mit MAs und ADX
Bestimmt Trendrichtung und -stärke
"""

from datetime import datetime
from typing import Dict, List, Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import BOT_WEIGHTS, INDICATOR_PARAMS


class TrendBot(BaseBot):
    """Trend Trading Bot - Moving Averages und ADX"""
    
    def __init__(self):
        super().__init__(name='Trend', weight=BOT_WEIGHTS.get('trend', 0.20))
        self.ma_periods = [9, 21, 50, 200]  # Multiple MAs
        self.adx_period = INDICATOR_PARAMS.get('adx', {}).get('period', 14)
        self.trend_threshold = INDICATOR_PARAMS.get('adx', {}).get('trend_threshold', 25)
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere Trend und generiere Signal
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            data_manager: DataManager Instanz
            
        Returns:
            Signal: Trading-Signal
        """
        try:
            # Hole Daten
            data = self._get_ohlcv_data(symbol, timeframe, data_manager, periods=250)
            
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
            
            # Berechne MAs
            ma_values = {}
            for period in self.ma_periods:
                ma_values[period] = self._calculate_sma(closes, period)
            
            # Berechne ADX
            adx, plus_di, minus_di = self._calculate_adx(highs, lows, closes, self.adx_period)
            
            # Analysiere Trend
            signal_type, confidence, action = self._analyze_trend(
                closes[-1], ma_values, adx, plus_di, minus_di
            )
            
            details = {
                'current_price': round(closes[-1], 2),
                'ma9': round(ma_values[9], 2),
                'ma21': round(ma_values[21], 2),
                'ma50': round(ma_values[50], 2),
                'ma200': round(ma_values[200], 2),
                'adx': round(adx, 2),
                'plus_di': round(plus_di, 2),
                'minus_di': round(minus_di, 2),
                'trend_strength': 'Strong' if adx > self.trend_threshold else 'Weak',
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
    
    def _analyze_trend(self, current_price: float, ma_values: Dict[int, float], 
                       adx: float, plus_di: float, minus_di: float) -> Tuple[SignalType, float, str]:
        """Analysiere Trend basierend auf MAs und ADX"""
        
        # Bestimme Trendrichtung
        # Bullish: Preis > MA21 > MA50 > MA200
        # Bearish: Preis < MA21 < MA50 < MA200
        
        ma9 = ma_values[9]
        ma21 = ma_values[21]
        ma50 = ma_values[50]
        ma200 = ma_values[200]
        
        bullish_alignment = (
            current_price > ma9 > ma21 > ma50 > ma200 or
            current_price > ma21 > ma50 > ma200
        )
        
        bearish_alignment = (
            current_price < ma9 < ma21 < ma50 < ma200 or
            current_price < ma21 < ma50 < ma200
        )
        
        # ADX bestimmt Trendstärke
        strong_trend = adx > self.trend_threshold
        
        if bullish_alignment and (strong_trend or plus_di > minus_di):
            # Bullisher Trend
            confidence = min(100, 50 + adx)
            if strong_trend:
                action = f'Bullish Trend (ADX: {adx:.1f})'
            else:
                action = f'Weak Bullish (ADX: {adx:.1f})'
            return SignalType.BUY, confidence, action
        
        elif bearish_alignment and (strong_trend or minus_di > plus_di):
            # Bärischer Trend
            confidence = min(100, 50 + adx)
            if strong_trend:
                action = f'Bearish Trend (ADX: {adx:.1f})'
            else:
                action = f'Weak Bearish (ADX: {adx:.1f})'
            return SignalType.SELL, confidence, action
        
        elif strong_trend:
            # Trend vorhanden aber keine klare Richtung
            if plus_di > minus_di:
                return SignalType.BUY, 40, f'Strong but unclear (ADX: {adx:.1f})'
            else:
                return SignalType.SELL, 40, f'Strong but unclear (ADX: {adx:.1f})'
        
        else:
            # Kein Trend - Seitwärtsmarkt
            return SignalType.HOLD, 30, f'Range-bound (ADX: {adx:.1f})'
    
    def __repr__(self) -> str:
        return f"TrendBot(ma_periods={self.ma_periods}, adx_period={self.adx_period})"