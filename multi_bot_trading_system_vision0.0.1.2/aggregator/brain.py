# filepath: aggregator/brain.py
"""
Brain - Signal Aggregation und Entscheidungsfindung
Aggregiert alle Bot-Signale zu einer finalen Entscheidung
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from bots.base_bot import BaseBot, Signal, SignalType
from config import BOT_WEIGHTS, SIGNAL_THRESHOLDS


logger = logging.getLogger(__name__)


@dataclass
class AggregatedSignal:
    """Aggregiertes Signal mit Details"""
    final_signal: SignalType
    confidence: float
    buy_score: float
    sell_score: float
    hold_score: float
    bot_signals: List[Signal]
    timestamp: datetime
    details: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'final_signal': self.final_signal.value,
            'confidence': self.confidence,
            'buy_score': round(self.buy_score, 2),
            'sell_score': round(self.sell_score, 2),
            'hold_score': round(self.hold_score, 2),
            'bot_signals': [s.to_dict() for s in self.bot_signals],
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }


class Brain:
    """Signal Aggregator - aggregiert alle Bot-Signale"""
    
    def __init__(self, bots: List[BaseBot]):
        self.bots = bots
        self.last_aggregated_signal: Optional[AggregatedSignal] = None
        self.signal_history: List[AggregatedSignal] = []
        self.max_history = 100
        
        # Bot Gewichte
        self.bot_weights = BOT_WEIGHTS.copy()
        
        # Schwellenwerte
        self.min_buy_prob = SIGNAL_THRESHOLDS.get('min_buy_probability', 65)
        self.min_sell_prob = SIGNAL_THRESHOLDS.get('min_sell_probability', 65)
        self.min_confidence = SIGNAL_THRESHOLDS.get('min_confidence', 60)
    
    def aggregate_signals(self, symbol: str, timeframe: str, data_manager) -> AggregatedSignal:
        """
        Aggregiere alle Bot-Signale zu einem finalen Signal
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            data_manager: DataManager Instanz
            
        Returns:
            AggregatedSignal: Aggregiertes Signal
        """
        try:
            # Sammle alle Signale
            bot_signals = []
            for bot in self.bots:
                if bot.is_enabled():
                    signal = bot.analyze(symbol, timeframe, data_manager)
                    bot_signals.append(signal)
            
            # Berechne gewichtete Scores
            buy_score = 0
            sell_score = 0
            hold_score = 0
            total_weight = 0
            
            for signal in bot_signals:
                # Hole Bot-Gewicht
                bot_weight = self._get_bot_weight(signal.bot_name)
                total_weight += bot_weight
                
                # Berechne Score basierend auf Signal-Typ
                if signal.signal_type == SignalType.BUY:
                    buy_score += signal.confidence * bot_weight
                elif signal.signal_type == SignalType.SELL:
                    sell_score += signal.confidence * bot_weight
                else:
                    hold_score += signal.confidence * bot_weight
            
            # Normalisiere Scores
            if total_weight > 0:
                buy_score = (buy_score / total_weight)
                sell_score = (sell_score / total_weight)
                hold_score = (hold_score / total_weight)
            
            # Bestimme finales Signal
            final_signal, confidence = self._determine_final_signal(
                buy_score, sell_score, hold_score
            )
            
            # Erstelle AggregatedSignal
            aggregated = AggregatedSignal(
                final_signal=final_signal,
                confidence=confidence,
                buy_score=buy_score,
                sell_score=sell_score,
                hold_score=hold_score,
                bot_signals=bot_signals,
                timestamp=datetime.now(),
                details={
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'active_bots': len([b for b in self.bots if b.is_enabled()]),
                    'min_buy_threshold': self.min_buy_prob,
                    'min_sell_threshold': self.min_sell_prob
                }
            )
            
            # Speichere in History
            self.last_aggregated_signal = aggregated
            self.signal_history.append(aggregated)
            if len(self.signal_history) > self.max_history:
                self.signal_history.pop(0)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating signals: {e}")
            return AggregatedSignal(
                final_signal=SignalType.HOLD,
                confidence=0,
                buy_score=0,
                sell_score=0,
                hold_score=100,
                bot_signals=[],
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def _get_bot_weight(self, bot_name: str) -> float:
        """Hole Bot-Gewicht"""
        # Normalisiere Bot-Namen
        name_lower = bot_name.lower()
        
        for key, weight in self.bot_weights.items():
            if key in name_lower or name_lower in key:
                return weight
        
        return 1.0  # Standard-Gewicht
    
    def _determine_final_signal(self, buy_score: float, sell_score: float, 
                                 hold_score: float) -> Tuple[SignalType, float]:
        """
        Bestimme finales Signal basierend auf Scores
        
        Args:
            buy_score: Buy Score (0-100)
            sell_score: Sell Score (0-100)
            hold_score: Hold Score (0-100)
            
        Returns:
            Tuple[SignalType, confidence]
        """
        # Berechne Gesamt-Konfidenz
        total = buy_score + sell_score + hold_score
        if total > 0:
            buy_pct = (buy_score / total) * 100
            sell_pct = (sell_score / total) * 100
            hold_pct = (hold_score / total) * 100
        else:
            buy_pct = sell_pct = hold_pct = 0
        
        # Bestimme Signal basierend auf Schwellenwerten
        if buy_pct >= self.min_buy_prob and buy_pct > sell_pct:
            # Buy Signal
            confidence = min(100, buy_pct)
            return SignalType.BUY, confidence
        
        elif sell_pct >= self.min_sell_prob and sell_pct > buy_pct:
            # Sell Signal
            confidence = min(100, sell_pct)
            return SignalType.SELL, confidence
        
        else:
            # Hold Signal
            confidence = max(hold_pct, 50)
            return SignalType.HOLD, confidence
    
    def get_bot_probabilities(self, symbol: str, timeframe: str, data_manager) -> Dict[str, Dict[str, float]]:
        """
        Hole Buy/Sell/Hold Wahrscheinlichkeiten für jeden Bot
        
        Returns:
            Dict: {bot_name: {'buy': %, 'sell': %, 'hold': %}}
        """
        probabilities = {}
        
        for bot in self.bots:
            if bot.is_enabled():
                try:
                    buy, sell, hold = bot.calculate_probabilities(symbol, timeframe, data_manager)
                    probabilities[bot.name] = {
                        'buy': round(buy, 2),
                        'sell': round(sell, 2),
                        'hold': round(hold, 2),
                        'last_signal': bot.last_signal.to_dict() if bot.last_signal else None
                    }
                except Exception as e:
                    logger.error(f"Error getting probabilities for {bot.name}: {e}")
                    probabilities[bot.name] = {
                        'buy': 0,
                        'sell': 0,
                        'hold': 100,
                        'error': str(e)
                    }
        
        return probabilities
    
    def get_last_signal(self) -> Optional[AggregatedSignal]:
        """Hole das letzte aggregierte Signal"""
        return self.last_aggregated_signal
    
    def get_signal_history(self, limit: int = 10) -> List[AggregatedSignal]:
        """Hole Signal-History"""
        return self.signal_history[-limit:]
    
    def enable_bot(self, bot_name: str):
        """Aktiviere einen Bot"""
        for bot in self.bots:
            if bot.name.lower() == bot_name.lower():
                bot.enable()
                logger.info(f"Enabled bot: {bot.name}")
                break
    
    def disable_bot(self, bot_name: str):
        """Deaktiviere einen Bot"""
        for bot in self.bots:
            if bot.name.lower() == bot_name.lower():
                bot.disable()
                logger.info(f"Disabled bot: {bot.name}")
                break
    
    def get_enabled_bots(self) -> List[str]:
        """Hole Liste der aktiven Bots"""
        return [bot.name for bot in self.bots if bot.is_enabled()]
    
    def __repr__(self) -> str:
        enabled = self.get_enabled_bots()
        return f"Brain(bots={len(self.bots)}, enabled={len(enabled)})"