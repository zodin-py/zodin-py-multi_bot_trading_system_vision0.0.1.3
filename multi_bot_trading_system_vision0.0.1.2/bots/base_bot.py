# filepath: bots/base_bot.py
"""
Base Bot - Abstrakte Basisklasse für alle Trading-Bots
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
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
    def analyze(self, symbol: str, timeframe: str, data_manager) -> Signal:
        """
        Analysiere Marktdaten und generiere ein Signal
        
        Args:
            symbol: Trading-Paar (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '1m', '5m', '1h')
            data_manager: DataManager Instanz für Marktdaten
            
        Returns:
            Signal: Trading-Signal mit Konfidenz
        """
        pass
    
    def calculate_probabilities(self, symbol: str, timeframe: str, data_manager) -> Tuple[float, float, float]:
        """
        Berechne Buy/Sell/Hold Wahrscheinlichkeiten
        
        Returns:
            Tuple[buy_prob, sell_prob, hold_prob]
        """
        try:
            signal = self.analyze(symbol, timeframe, data_manager)
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
    
    def _get_ohlcv_data(self, symbol: str, timeframe: str, data_manager, periods: int = 50) -> Optional[dict]:
        """Hole OHLCV Daten"""
        ohlcv = data_manager.get_ohlcv(symbol, timeframe, periods)
        if ohlcv is None:
            return None
        
        opens, highs, lows, closes, volumes = ohlcv
        
        return {
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes,
            'volumes': volumes
        }
    
    def _calculate_ema(self, data: List[float], period: int) -> float:
        """Berechne Exponential Moving Average"""
        if len(data) < period:
            return data[-1] if data else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period
        
        for value in data[period:]:
            ema = (value - ema) * multiplier + ema
        
        return ema
    
    def _calculate_sma(self, data: List[float], period: int) -> float:
        """Berechne Simple Moving Average"""
        if len(data) < period:
            return data[-1] if data else 0
        
        return sum(data[-period:]) / period
    
    def _calculate_rma(self, data: List[float], period: int) -> float:
        """
        Berechne Wilder's Moving Average (RMA) - wie TradingView
        Wird für RSI verwendet
        """
        if len(data) < period:
            return 0
        
        # Erste RMA ist ein Simple Moving Average
        rma = sum(data[:period]) / period
        
        # Berechne RMA für den Rest der Daten mit Wilder's Smoothing
        for i in range(period, len(data)):
            rma = (rma * (period - 1) + data[i]) / period
        
        return rma
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """
        Berechne RSI wie TradingView (mit Wilder's Moving Average)
        
        Formel:
        change = close[i] - close[i-1]
        up = RMA(max(change, 0), period)
        down = RMA(max(-change, 0), period)
        rsi = 100 - (100 / (1 + up/down))
        """
        if len(closes) < period + 1:
            return 50
        
        # Berechne Änderungen
        changes = []
        for i in range(1, len(closes)):
            changes.append(closes[i] - closes[i-1])
        
        # Positive Änderungen (Gains)
        ups = [max(change, 0) for change in changes]
        
        # Negative Änderungen (Losses) - als positive Werte
        downs = [abs(min(change, 0)) for change in changes]
        
        # Berechne RMA (Wilder's Moving Average)
        up_rma = self._calculate_rma(ups, period)
        down_rma = self._calculate_rma(downs, period)
        
        # Berechne RSI
        if down_rma == 0:
            if up_rma == 0:
                return 50
            return 100
        
        if up_rma == 0:
            return 0
        
        rs = up_rma / down_rma
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, closes: List[float]) -> Tuple[float, float, float]:
        """Berechne MACD (MACD Line, Signal Line, Histogram)"""
        if len(closes) < 26:
            return 0, 0, 0
        
        ema12 = self._calculate_ema(closes, 12)
        ema26 = self._calculate_ema(closes, 26)
        macd_line = ema12 - ema26
        
        # Signal Line (9-period EMA of MACD)
        signal_line = macd_line  # Vereinfacht
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_mfi(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float], period: int = 14) -> float:
        """Berechne Money Flow Index"""
        if len(closes) < period + 1:
            return 50
        
        typical_prices = []
        money_flow = []
        
        for i in range(len(closes)):
            tp = (highs[i] + lows[i] + closes[i]) / 3
            typical_prices.append(tp)
            money_flow.append(tp * volumes[i])
        
        positive_flow = 0
        negative_flow = 0
        
        for i in range(1, len(typical_prices)):
            if typical_prices[i] > typical_prices[i-1]:
                positive_flow += money_flow[i]
            else:
                negative_flow += money_flow[i]
        
        if negative_flow == 0:
            return 100
        
        money_ratio = positive_flow / negative_flow
        mfi = 100 - (100 / (1 + money_ratio))
        
        return mfi
    
    def _calculate_adx(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Tuple[float, float, float]:
        """Berechne ADX (Average Directional Index)"""
        if len(closes) < period + 1:
            return 0, 0, 0
        
        plus_dm = []
        minus_dm = []
        true_range = []
        
        for i in range(1, len(closes)):
            high_diff = highs[i] - highs[i-1]
            low_diff = lows[i-1] - lows[i]
            
            plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
            minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)
            
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_range.append(tr)
        
        if len(true_range) < period:
            return 0, 0, 0
        
        # Vereinfachte ADX Berechnung
        avg_tr = sum(true_range[-period:]) / period
        plus_di = (sum(plus_dm[-period:]) / avg_tr) * 100 if avg_tr > 0 else 0
        minus_di = (sum(minus_dm[-period:]) / avg_tr) * 100 if avg_tr > 0 else 0
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        
        return dx, plus_di, minus_di
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, enabled={self.enabled})"