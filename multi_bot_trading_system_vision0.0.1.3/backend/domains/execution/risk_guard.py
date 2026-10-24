"""Risk guard — pre-trade checks for limits, cooldowns, and halt conditions."""

from __future__ import annotations

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RiskGuard:
    """Pre-trade risk checks: daily loss limit, cooldown, position limits."""

    def __init__(
        self,
        max_daily_loss: float = 10.0,
        trade_cooldown_sec: int = 60,
        max_open_trades: int = 5,
    ):
        self.max_daily_loss = max_daily_loss
        self.trade_cooldown_sec = trade_cooldown_sec
        self.max_open_trades = max_open_trades
        self._daily_pnl: float = 0.0
        self._last_trade_time: Dict[str, float] = {}  # symbol -> timestamp

    def check_daily_limit(self, daily_pnl: float) -> bool:
        """Return True if daily loss limit NOT exceeded."""
        return daily_pnl > -self.max_daily_loss

    def check_cooldown(self, symbol: str) -> bool:
        """Return True if symbol is NOT in cooldown."""
        import time
        last_time = self._last_trade_time.get(symbol, 0)
        return (time.time() - last_time) >= self.trade_cooldown_sec

    def record_trade(self, symbol: str) -> None:
        """Record trade time for cooldown tracking."""
        import time
        self._last_trade_time[symbol] = time.time()

    def check_max_positions(self, open_count: int) -> bool:
        """Return True if under max open positions."""
        return open_count < self.max_open_trades

    def get_halt_reason(self, daily_pnl: float, open_count: int) -> Optional[str]:
        """Return halt reason if trading should be halted, else None."""
        if daily_pnl <= -self.max_daily_loss:
            return 'daily_loss_limit'
        if open_count >= self.max_open_trades:
            return 'max_positions'
        return None
