"""Execution service — orchestrates order placement, position sizing, SL/TP, and risk checks."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.domains.execution.models import OrderSide, OrderType, Trade, TradeStatus
from backend.domains.execution.order_executor import OrderExecutor
from backend.domains.execution.position_sizer import PositionSizer
from backend.domains.execution.risk_guard import RiskGuard
from backend.domains.execution.sl_tp_calculator import SLTPCalculator
from backend.domains.execution.repository import TradeRepository

logger = logging.getLogger(__name__)


class ExecutionService:
    """Orchestrates trade execution with risk checks."""

    def __init__(
        self,
        repository: Optional[TradeRepository] = None,
        order_executor: Optional[OrderExecutor] = None,
        position_sizer: Optional[PositionSizer] = None,
        risk_guard: Optional[RiskGuard] = None,
        sl_tp_calculator: Optional[SLTPCalculator] = None,
        capital: float = 10000.0,
    ):
        self._repository = repository or TradeRepository()
        self._executor = order_executor or OrderExecutor()
        self._sizer = position_sizer or PositionSizer()
        self._risk = risk_guard or RiskGuard()
        self._sl_tp = sl_tp_calculator or SLTPCalculator()
        self._capital = capital
        self._daily_pnl: float = 0.0

    @property
    def capital(self) -> float:
        return self._capital

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl

    def open_trade(
        self,
        symbol: str,
        timeframe: str,
        side: str,
        entry_price: float,
        sr_levels: Optional[List[float]] = None,
        atr: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """Open a new trade with full execution flow."""
        # Risk checks
        if not self._risk.check_daily_limit(self._daily_pnl):
            return {'error': 'Daily loss limit reached'}
        if not self._risk.check_max_positions(len(self._repository.get_open_trades())):
            return {'error': 'Max open trades reached'}
        if not self._risk.check_cooldown(symbol):
            return {'error': f'Cooldown active for {symbol}'}

        # Calculate SL/TP
        sl, tp, sl_source = self._sl_tp.calculate(entry_price, side, sr_levels, atr)
        if sl <= 0 or tp <= 0:
            return {'error': 'Invalid SL/TP calculation'}

        # Calculate position size
        quantity = self._sizer.calculate_size(self._capital, entry_price, sl)
        if quantity <= 0:
            return {'error': 'Invalid position size'}

        # Place order
        order = self._executor.place_market_order(symbol, side, quantity)
        if not order:
            return {'error': 'Order placement failed'}

        # Create trade record
        trade_id = str(uuid.uuid4())
        trade = Trade(
            id=trade_id,
            symbol=symbol,
            timeframe=timeframe,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=sl,
            take_profit=tp,
            status=TradeStatus.OPEN,
            open_time=datetime.now(),
            sl_source=sl_source,
        )
        self._repository.add_trade(trade)
        self._risk.record_trade(symbol)

        logger.info(f"Opened trade: {trade_id} {side} {symbol} @ {entry_price}")
        return trade.to_dict()

    def close_trade(self, trade_id: str, reason: str = 'manual') -> Optional[Dict[str, Any]]:
        """Close an open trade."""
        trade = self._repository.get_trade(trade_id)
        if not trade:
            return {'error': 'Trade not found'}

        # P&L calculation (placeholder if no current price)
        pnl = 0.0
        pnl_percent = 0.0
        if trade.side == 'long':
            pnl = (trade.entry_price - trade.stop_loss) * trade.quantity  # simplified
        else:
            pnl = (trade.stop_loss - trade.entry_price) * trade.quantity

        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.status = TradeStatus.CLOSED
        trade.close_time = datetime.now()
        trade.notes = reason

        self._capital += pnl
        self._daily_pnl += pnl
        self._repository.add_trade(trade)

        logger.info(f"Closed trade: {trade_id} P&L: {pnl:.2f}")
        return trade.to_dict()

    def get_open_trades(self) -> List[Dict[str, Any]]:
        """Get all open trades."""
        return [t.to_dict() for t in self._repository.get_open_trades()]

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """Get trade history."""
        return [t.to_dict() for t in self._repository.get_history()]

    def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio status."""
        halt_reason = self._risk.get_halt_reason(self._daily_pnl, len(self._repository.get_open_trades()))
        return {
            'capital': round(self._capital, 2),
            'daily_pnl': round(self._daily_pnl, 2),
            'open_count': len(self._repository.get_open_trades()),
            'is_halted': halt_reason is not None,
            'halt_reason': halt_reason,
            'max_open_trades': self._sizer.max_open_trades,
            'trade_cooldown_sec': self._risk.trade_cooldown_sec,
        }

    def check_conditions(self, symbol: str, current_price: float) -> List[str]:
        """Check which open trades need closing (SL/TP hit)."""
        to_close = []
        for trade in self._repository.get_open_trades():
            if trade.symbol != symbol:
                continue
            if trade.side == 'long':
                if current_price >= trade.take_profit:
                    to_close.append((trade.id, 'TP'))
                elif current_price <= trade.stop_loss:
                    to_close.append((trade.id, 'SL'))
            else:
                if current_price <= trade.take_profit:
                    to_close.append((trade.id, 'TP'))
                elif current_price >= trade.stop_loss:
                    to_close.append((trade.id, 'SL'))
        return [tid for tid, _ in to_close]
