"""Portfolio domain models — Portfolio, CapitalSnapshot, DailyPnL, OpenPosition."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class OpenPosition:
    """Represents an open trade position."""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: float
    open_time: datetime
    bot_name: str = ''

    def to_dict(self) -> dict:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'stop_loss': round(self.stop_loss, 8),
            'take_profit': round(self.take_profit, 8),
            'open_time': self.open_time.isoformat(),
            'bot_name': self.bot_name,
        }


@dataclass
class DailyPnL:
    """Daily P&L tracking entry."""
    date: str
    pnl: float
    trades_count: int = 0
    wins: int = 0
    losses: int = 0

    def to_dict(self) -> dict:
        return {
            'date': self.date,
            'pnl': round(self.pnl, 2),
            'trades_count': self.trades_count,
            'wins': self.wins,
            'losses': self.losses,
        }


@dataclass
class CapitalSnapshot:
    """Point-in-time capital snapshot."""
    timestamp: datetime
    capital: float
    equity: float
    daily_pnl: float
    open_count: int

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'capital': round(self.capital, 2),
            'equity': round(self.equity, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'open_count': self.open_count,
        }


@dataclass
class Portfolio:
    """Current portfolio state."""
    total_capital: float
    daily_pnl: float
    total_pnl: float
    open_trades_count: int
    positions: List[OpenPosition] = field(default_factory=list)
    daily_history: List[DailyPnL] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'total_capital': round(self.total_capital, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'total_pnl': round(self.total_pnl, 2),
            'open_trades_count': self.open_trades_count,
            'positions': [p.to_dict() for p in self.positions],
            'daily_history': [d.to_dict() for d in self.daily_history[-7:]],
        }
