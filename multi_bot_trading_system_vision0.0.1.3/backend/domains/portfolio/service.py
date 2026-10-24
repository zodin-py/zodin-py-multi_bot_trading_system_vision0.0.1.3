"""Portfolio domain service — tracks capital, P&L, positions."""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import List, Optional

from backend.domains.portfolio.models import (
    CapitalSnapshot, DailyPnL, OpenPosition, Portfolio
)

logger = logging.getLogger(__name__)


class PortfolioService:
    """Manages portfolio state: capital, P&L, open positions."""

    def __init__(self, initial_capital: float = 10000.0):
        self._capital = initial_capital
        self._daily_pnl: float = 0.0
        self._total_pnl: float = 0.0
        self._daily_date: str = date.today().isoformat()
        self._daily_history: dict = {}
        self._positions: dict = {}
        self._open_count = 0
        self._snapshots: List[CapitalSnapshot] = []

    @property
    def capital(self) -> float:
        return self._capital

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl

    @property
    def total_pnl(self) -> float:
        return self._total_pnl

    @property
    def open_count(self) -> int:
        return self._open_count

    def reset_daily(self) -> bool:
        """Reset daily counters; returns True if day changed."""
        today = date.today().isoformat()
        if self._daily_date != today:
            self._daily_pnl = 0.0
            self._daily_date = today
            return True
        return False

    def add_open_position(self, trade_id: str, symbol: str, side: str,
                          entry_price: float, quantity: float,
                          stop_loss: float, take_profit: float,
                          open_time: datetime, bot_name: str = '') -> None:
        pos = OpenPosition(
            trade_id=trade_id, symbol=symbol, side=side,
            entry_price=entry_price, quantity=quantity,
            stop_loss=stop_loss, take_profit=take_profit,
            open_time=open_time, bot_name=bot_name,
        )
        self._positions[trade_id] = pos
        self._open_count += 1
        self._take_snapshot()

    def close_position(self, trade_id: str, pnl: float) -> Optional[DailyPnL]:
        """Track a closed trade and update P&L."""
        pos = self._positions.pop(trade_id, None)
        if pos is None:
            return None
        self._open_count = max(0, self._open_count - 1)

        today = date.today().isoformat()
        if today not in self._daily_history:
            self._daily_history[today] = DailyPnL(date=today, pnl=0.0)
        daily = self._daily_history[today]
        daily.pnl += pnl
        daily.trades_count += 1
        if pnl > 0:
            daily.wins += 1
        else:
            daily.losses += 1

        self._daily_pnl += pnl
        self._total_pnl += pnl
        self._take_snapshot()
        logger.info(f"Portfolio closed {trade_id}: P&L={pnl:.2f}, daily_pnl={self._daily_pnl:.2f}")
        return daily

    def get_portfolio(self) -> Portfolio:
        """Get current portfolio snapshot."""
        return Portfolio(
            total_capital=self._capital,
            daily_pnl=self._daily_pnl,
            total_pnl=self._total_pnl,
            open_trades_count=self._open_count,
            positions=list(self._positions.values()),
            daily_history=list(self._daily_history.values()),
        )

    def _take_snapshot(self) -> None:
        snap = CapitalSnapshot(
            timestamp=datetime.now(),
            capital=self._capital,
            equity=self._capital + self._daily_pnl,
            daily_pnl=self._daily_pnl,
            open_count=self._open_count,
        )
        self._snapshots.append(snap)
        if len(self._snapshots) > 1000:
            self._snapshots.pop(0)

    def can_open_trade(self) -> bool:
        """Check if a new trade can be opened."""
        return self._open_count < 5  # reasonable default
