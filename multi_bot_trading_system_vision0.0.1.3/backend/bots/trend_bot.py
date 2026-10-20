# filepath: bots/trend_bot.py
"""
Trend Bot - Trendanalyse mit MAs und ADX
Bestimmt Trendrichtung und -stärke

Liest vorberechnete Indikatoren aus dem IndicatorProvider.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional

from backend.bots.base_bot import BaseBot, Signal, SignalType
from backend.config import BOT_WEIGHTS, INDICATOR_PARAMS
from backend.indicators.provider import IndicatorProvider


class TrendBot(BaseBot):
    """Trend Trading Bot - Moving Averages und ADX"""

    def __init__(self, provider: Optional[IndicatorProvider] = None):
        super().__init__(name='Trend', weight=BOT_WEIGHTS.get('trend', 0.20))
        self.ma_periods = [9, 21, 50, 200]  # Multiple MAs
        self.adx_period = INDICATOR_PARAMS.get('adx', {}).get('period', 14)
        self.trend_threshold = INDICATOR_PARAMS.get('adx', {}).get('trend_threshold', 25)
        self._provider = provider

    @property
    def provider(self) -> Optional[IndicatorProvider]:
        return self._provider

    @provider.setter
    def provider(self, provider: IndicatorProvider):
        self._provider = provider

    def analyze(self, symbol: str, timeframe: str, provider: IndicatorProvider) -> Signal:
        """
        Analysiere Trend und generiere Signal

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

            # Prüfe auf veraltete Daten
            if provider.is_stale(symbol, timeframe):
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'Stale data'}
                )

            # Hole vorberechnete Werte
            adx = indicators.get('adx')
            plus_di = indicators.get('plus_di')
            minus_di = indicators.get('minus_di')
            ema_9 = indicators.get('ema_9')
            ema_21 = indicators.get('ema_21')
            ema_50 = indicators.get('ema_50')
            ema_200 = indicators.get('ema_200')
            sma_20 = indicators.get('sma_20')
            sma_50 = indicators.get('sma_50')

            if adx is None or plus_di is None or minus_di is None:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'Trend indicators not available'}
                )

            # Hole aktuellen Preis
            ohlcv = provider.get_ohlcv(symbol, timeframe, periods=2)
            if ohlcv is None:
                return Signal(
                    bot_name=self.name,
                    signal_type=SignalType.HOLD,
                    confidence=0,
                    timestamp=datetime.now(),
                    details={'error': 'No price data'}
                )
            current_price = ohlcv[3][-1]  # closes[-1]

            ma_values = {
                9: ema_9 if ema_9 is not None else current_price,
                21: ema_21 if ema_21 is not None else current_price,
                50: ema_50 if ema_50 is not None else current_price,
                200: ema_200 if ema_200 is not None else current_price,
            }

            # Analysiere Trend
            signal_type, confidence, action = self._analyze_trend(
                current_price, ma_values, adx, plus_di, minus_di
            )

            details = {
                'current_price': round(current_price, 2),
                'ema_9': round(ema_9, 2) if ema_9 else None,
                'ema_21': round(ema_21, 2) if ema_21 else None,
                'ema_50': round(ema_50, 2) if ema_50 else None,
                'ema_200': round(ema_200, 2) if ema_200 else None,
                'sma_20': round(sma_20, 2) if sma_20 else None,
                'sma_50': round(sma_50, 2) if sma_50 else None,
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