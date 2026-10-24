"""Execution domain models — Trade, Order, Position, Status."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TradeStatus(Enum):
    OPEN = 'open'
    CLOSED = 'closed'
    CANCELLED = 'cancelled'


class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'


class OrderType(Enum):
    MARKET = 'market'
    LIMIT = 'limit'


@dataclass
class Trade:
    """Represents a single trade position."""
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
    pnl: float = 0.0
    pnl_percent: float = 0.0
    notes: str = ''
    sl_source: str = ''  # 'sr_level' or 'atr_fallback'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'stop_loss': round(self.stop_loss, 8),
            'take_profit': round(self.take_profit, 8),
            'status': self.status.value,
            'open_time': self.open_time.isoformat(),
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'pnl': round(self.pnl, 2),
            'pnl_percent': round(self.pnl_percent, 2),
            'notes': self.notes,
            'sl_source': self.sl_source,
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
            notes=data.get('notes', ''),
            sl_source=data.get('sl_source', ''),
        )


@dataclass
class Order:
    """Represents a placed order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float
    quantity: float
    status: str = 'pending'
    filled_quantity: float = 0.0
    fill_price: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'price': self.price,
            'quantity': self.quantity,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'fill_price': self.fill_price,
            'error': self.error,
        }


@dataclass
class Position:
    """Represents an open position."""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    unrealized_pnl: float = 0.0
