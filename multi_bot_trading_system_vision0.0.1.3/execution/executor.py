# filepath: execution/executor.py
"""
Executor - Trade Execution mit Stop-Loss & Take-Profit
Verwaltet offene Trades und führt Orders aus
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from bots.base_bot import SignalType
from config import RISK_PERCENT, RISK_REWARD_RATIO, TRADES_HISTORY_FILE, INITIAL_CAPITAL


logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Trade Status"""
    OPEN = 'open'
    CLOSED = 'closed'
    CANCELLED = 'cancelled'


@dataclass
class Trade:
    """Trade Object"""
    id: str
    symbol: str
    timeframe: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    status: TradeStatus
    open_time: datetime
    close_time: Optional[datetime] = None
    pnl: float = 0
    pnl_percent: float = 0
    notes: str = ''
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'status': self.status.value,
            'open_time': self.open_time.isoformat(),
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'pnl': round(self.pnl, 2),
            'pnl_percent': round(self.pnl_percent, 2),
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Trade':
        return cls(
            id=data['id'],
            symbol=data['symbol'],
            timeframe=data['timeframe'],
            side=data['side'],
            entry_price=data['entry_price'],
            quantity=data['quantity'],
            stop_loss=data['stop_loss'],
            take_profit=data['take_profit'],
            status=TradeStatus(data['status']),
            open_time=datetime.fromisoformat(data['open_time']),
            close_time=datetime.fromisoformat(data['close_time']) if data.get('close_time') else None,
            pnl=data.get('pnl', 0),
            pnl_percent=data.get('pnl_percent', 0),
            notes=data.get('notes', '')
        )


class Executor:
    """Trade Executor - führt Trades aus und verwaltet sie"""
    
    def __init__(self, capital: float = INITIAL_CAPITAL):
        self.capital = capital
        self.open_trades: Dict[str, Trade] = {}
        self.trade_history: List[Trade] = []
        self.trade_counter = 0
        
        # Lade existierende Trades
        self._load_trades()
    
    def _load_trades(self):
        """Lade Trades aus der History-Datei"""
        try:
            if os.path.exists(TRADES_HISTORY_FILE):
                with open(TRADES_HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    for trade_data in data:
                        trade = Trade.from_dict(trade_data)
                        if trade.status == TradeStatus.OPEN:
                            self.open_trades[trade.id] = trade
                        else:
                            self.trade_history.append(trade)
                    
                    # Setze Trade-Counter
                    if self.trade_history:
                        max_id = max([int(t.id.replace('TRD', '')) for t in self.trade_history if t.id.startswith('TRD')], default=0)
                        self.trade_counter = max_id
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
    
    def _save_trades(self):
        """Speichere Trades in die History-Datei"""
        try:
            # Erstelle Verzeichnis falls nicht vorhanden
            os.makedirs(os.path.dirname(TRADES_HISTORY_FILE), exist_ok=True)
            
            # Sammle alle geschlossenen Trades
            all_trades = self.trade_history + list(self.open_trades.values())
            
            with open(TRADES_HISTORY_FILE, 'w') as f:
                json.dump([t.to_dict() for t in all_trades], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trades: {e}")
    
    def calculate_position_size(self, symbol: str, entry_price: float, 
                                stop_loss: float) -> float:
        """
        Berechne Positionsgröße basierend auf Risk Management
        
        Args:
            symbol: Trading-Paar
            entry_price: Einstiegspreis
            stop_loss: Stop-Loss Preis
            
        Returns:
            float: Positionsgröße
        """
        # Berechne Risk Amount
        risk_amount = self.capital * (RISK_PERCENT / 100)
        
        # Berechne SL Distance
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            return 0
        
        # Berechne Positionsgröße
        quantity = risk_amount / sl_distance
        
        return quantity
    
    def open_trade(self, symbol: str, timeframe: str, signal: SignalType,
                   entry_price: float, data_manager) -> Optional[Trade]:
        """
        Öffne einen neuen Trade
        
        Args:
            symbol: Trading-Paar
            timeframe: Timeframe
            signal: Signal-Typ (BUY oder SELL)
            entry_price: Einstiegspreis
            data_manager: DataManager Instanz
            
        Returns:
            Trade oder None
        """
        try:
            # Bestimme Seite
            if signal == SignalType.BUY:
                side = 'long'
            elif signal == SignalType.SELL:
                side = 'short'
            else:
                return None
            
            # Berechne SL und TP
            if side == 'long':
                stop_loss = entry_price * (1 - RISK_PERCENT / 100)
                take_profit = entry_price * (1 + (RISK_PERCENT * RISK_REWARD_RATIO) / 100)
            else:
                stop_loss = entry_price * (1 + RISK_PERCENT / 100)
                take_profit = entry_price * (1 - (RISK_PERCENT * RISK_REWARD_RATIO) / 100)
            
            # Berechne Positionsgröße
            quantity = self.calculate_position_size(symbol, entry_price, stop_loss)
            
            if quantity <= 0:
                logger.warning(f"Invalid position size for {symbol}")
                return None
            
            # Erstelle Trade
            self.trade_counter += 1
            trade = Trade(
                id=f"TRD{self.trade_counter:05d}",
                symbol=symbol,
                timeframe=timeframe,
                side=side,
                entry_price=entry_price,
                quantity=quantity,
                stop_loss=round(stop_loss, 2),
                take_profit=round(take_profit, 2),
                status=TradeStatus.OPEN,
                open_time=datetime.now()
            )
            
            # Speichere Trade
            self.open_trades[trade.id] = trade
            self._save_trades()
            
            logger.info(f"Opened trade: {trade.id} - {side} {symbol} at {entry_price}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error opening trade: {e}")
            return None
    
    def close_trade(self, trade_id: str, reason: str = 'manual') -> Optional[Trade]:
        """
        Schließe einen Trade
        
        Args:
            trade_id: Trade ID
            reason: Schließungsgrund
            
        Returns:
            Trade oder None
        """
        if trade_id not in self.open_trades:
            logger.warning(f"Trade {trade_id} not found")
            return None
        
        trade = self.open_trades[trade_id]
        
        # Hole aktuellen Preis (würde in echtem Trading von API kommen)
        # Hier simulieren wir nur
        current_price = trade.entry_price  # Placeholder
        
        # Berechne P&L
        if trade.side == 'long':
            pnl = (current_price - trade.entry_price) * trade.quantity
            pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100
        else:
            pnl = (trade.entry_price - current_price) * trade.quantity
            pnl_percent = ((trade.entry_price - current_price) / trade.entry_price) * 100
        
        # Update Trade
        trade.status = TradeStatus.CLOSED
        trade.close_time = datetime.now()
        trade.pnl = round(pnl, 2)
        trade.pnl_percent = round(pnl_percent, 2)
        trade.notes = reason
        
        # Update Capital
        self.capital += pnl
        
        # Verschiebe in History
        del self.open_trades[trade_id]
        self.trade_history.append(trade)
        self._save_trades()
        
        logger.info(f"Closed trade: {trade.id} - P&L: {pnl:.2f} ({pnl_percent:.2f}%)")
        
        return trade
    
    def check_trade_conditions(self, symbol: str, current_price: float) -> List[str]:
        """
        Prüfe SL/TP Bedingungen für alle offenen Trades eines Symbols
        
        Returns:
            List: Liste von Trade-IDs die geschlossen werden sollen
        """
        trades_to_close = []
        
        for trade_id, trade in self.open_trades.items():
            if trade.symbol != symbol:
                continue
            
            if trade.side == 'long':
                # Long: TP wenn Preis >= TP, SL wenn Preis <= SL
                if current_price >= trade.take_profit:
                    trades_to_close.append(trade_id)
                elif current_price <= trade.stop_loss:
                    trades_to_close.append(trade_id)
            else:
                # Short: TP wenn Preis <= TP, SL wenn Preis >= SL
                if current_price <= trade.take_profit:
                    trades_to_close.append(trade_id)
                elif current_price >= trade.stop_loss:
                    trades_to_close.append(trade_id)
        
        return trades_to_close
    
    def get_open_trades(self) -> List[Trade]:
        """Hole alle offenen Trades"""
        return list(self.open_trades.values())
    
    def get_trade_history(self, start_date: datetime = None, 
                         end_date: datetime = None) -> List[Trade]:
        """Hole Trade-History mit optionalem Datumsfilter"""
        trades = self.trade_history
        
        if start_date:
            trades = [t for t in trades if t.open_time >= start_date]
        
        if end_date:
            trades = [t for t in trades if t.open_time <= end_date]
        
        return trades
    
    def get_performance_stats(self, start_date: datetime = None,
                            end_date: datetime = None) -> dict:
        """Berechne Performance-Statistiken"""
        trades = self.get_trade_history(start_date, end_date)
        
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0,
                'avg_win': 0,
                'avg_loss': 0
            }
        
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in trades)
        total_pnl_percent = sum(t.pnl_percent for t in trades)
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(trades) * 100) if trades else 0,
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(total_pnl_percent, 2),
            'avg_win': round(sum(t.pnl for t in winning) / len(winning), 2) if winning else 0,
            'avg_loss': round(sum(t.pnl for t in losing) / len(losing), 2) if losing else 0
        }
    
    def __repr__(self) -> str:
        return f"Executor(open_trades={len(self.open_trades)}, capital={self.capital:.2f})"