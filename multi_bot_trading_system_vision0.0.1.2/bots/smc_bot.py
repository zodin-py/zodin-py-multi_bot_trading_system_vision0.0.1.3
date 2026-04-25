# filepath: bots/smc_bot.py
"""
SMC Bot - Smart Money Concepts
Erkennt Orderblocks und Fair Value Gaps (FVG)
"""

from datetime import datetime
from typing import Dict, List, Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import BOT_WEIGHTS


class SMCBot(BaseBot):
    """Smart Money Concepts Trading Bot"""
    
    def __init__(self):
        super().__init__(name='SMC', weight=BOT_WEIGHTS.get('smc', 0.15))
        self.lookback_period = 100
        self.fvg_threshold = 0.5  # % für FVG Erkennung
    
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere SMC Patterns und generiere Signal
        
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
            
            if data is None or len(data['closes']) < 20:
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
            volumes = data['volumes']
            
            # Finde Orderblocks
            buy_ob, sell_ob = self._find_orderblocks(closes, highs, lows, volumes)
            
            # Finde FVGs
            bullish_fvg, bearish_fvg = self._find_fvgs(highs, lows, closes)
            
            # Generiere Signal
            signal_type, confidence, action = self._analyze_smc(
                closes[-1], buy_ob, sell_ob, bullish_fvg, bearish_fvg
            )
            
            details = {
                'current_price': round(closes[-1], 2),
                'buy_orderblocks': [round(ob, 2) for ob in buy_ob[:3]],
                'sell_orderblocks': [round(ob, 2) for ob in sell_ob[:3]],
                'bullish_fvg': bullish_fvg,
                'bearish_fvg': bearish_fvg,
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
    
    def _find_orderblocks(self, closes: List[float], highs: List[float], lows: List[float], volumes: List[float]) -> Tuple[List[float], List[float]]:
        """Finde Bullish und Bearish Orderblocks"""
        buy_orderblocks = []
        sell_orderblocks = []
        
        for i in range(2, len(closes) - 2):
            # Bullish Orderblock: Nach einem Run-up, tieferer Tiefe mit hohem Volumen
            if closes[i] > closes[i-2] and closes[i+1] < closes[i]:
                # Finde tiefe Kerze mit hohem Volumen
                if volumes[i] > sum(volumes[max(0,i-5):i]) / 5:
                    if lows[i] < min(closes[i-2:i]):
                        buy_orderblocks.append(lows[i])
            
            # Bearish Orderblock: Nach einem Run-down, höheres Hoch mit hohem Volumen
            if closes[i] < closes[i-2] and closes[i+1] > closes[i]:
                if volumes[i] > sum(volumes[max(0,i-5):i]) / 5:
                    if highs[i] > max(closes[i-2:i]):
                        sell_orderblocks.append(highs[i])
        
        return buy_orderblocks[-5:], sell_orderblocks[-5:]
    
    def _find_fvgs(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[bool, bool]:
        """Finde Fair Value Gaps"""
        bullish_fvg = False
        bearish_fvg = False
        
        for i in range(2, len(closes) - 2):
            # Bullish FVG: Gap zwischen low[i-2] und high[i]
            gap_up = highs[i] - lows[i-2]
            if gap_up > 0 and gap_up / closes[i-2] > self.fvg_threshold / 100:
                # Prüfe ob Preis zurückkommt
                if closes[i+1] < closes[i]:
                    bullish_fvg = True
            
            # Bearish FVG: Gap zwischen high[i-2] und low[i]
            gap_down = highs[i-2] - lows[i]
            if gap_down > 0 and gap_down / closes[i-2] > self.fvg_threshold / 100:
                if closes[i+1] > closes[i]:
                    bearish_fvg = True
        
        return bullish_fvg, bearish_fvg
    
    def _analyze_smc(self, current_price: float, buy_ob: List[float], sell_ob: List[float], 
                     bullish_fvg: bool, bearish_fvg: bool) -> Tuple[SignalType, float, str]:
        """Analysiere SMC Signale"""
        
        buy_score = 0
        sell_score = 0
        
        # Prüfe Orderblocks
        for ob in buy_ob:
            if current_price > ob and (current_price - ob) / ob < 0.02:  # Innerhalb 2%
                buy_score += 30
        
        for ob in sell_ob:
            if current_price < ob and (ob - current_price) / ob < 0.02:
                sell_score += 30
        
        # Prüfe FVGs
        if bullish_fvg:
            buy_score += 25
        if bearish_fvg:
            sell_score += 25
        
        # Bestimme Signal
        if buy_score > sell_score and buy_score > 30:
            confidence = min(100, buy_score)
            return SignalType.BUY, confidence, f'Bullish SMC (Score: {buy_score})'
        elif sell_score > buy_score and sell_score > 30:
            confidence = min(100, sell_score)
            return SignalType.SELL, confidence, f'Bearish SMC (Score: {sell_score})'
        else:
            return SignalType.HOLD, 50, 'No clear SMC signal'
    
    def __repr__(self) -> str:
        return f"SMCBot(lookback={self.lookback_period})"