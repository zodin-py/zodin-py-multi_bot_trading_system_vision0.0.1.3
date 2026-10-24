"""Risk domain service — pre-trade risk checks and trading halt management."""

from __future__ import annotations

import logging
import time
from typing import Optional

from backend.config import MAX_DAILY_LOSS, TRADE_COOLDOWN_SEC, MAX_OPEN_TRADES
from backend.domains.risk.models import HaltReason, RiskState

logger = logging.getLogger(__name__)


class RiskService:
    """Manages risk limits, trading halt state, and cooldown enforcement."""

    def __init__(
        self,
        max_daily_loss: float = MAX_DAILY_LOSS,
        trade_cooldown_sec: int = TRADE_COOLDOWN_SEC,
        max_open_trades: int = MAX_OPEN_TRADES,
    ):
        self.max_daily_loss = max_daily_loss
        self.trade_cooldown_sec = trade_cooldown_sec
        self.max_open_trades = max_open_trades
        self._daily_pnl: float = 0.0
        self._last_trade_time: dict = {}  # symbol -> timestamp
        self._halted: bool = False
        self._halt_reason: Optional[HaltReason] = None

    @property
    def is_halted(self) -> bool:
        return self._halted

    @property
    def halt_reason(self) -> Optional[HaltReason]:
        return self._halt_reason

    @property
    def daily_pnl(self) -> float:
        return self._daily_pnl

    def record_daily_pnl(self, pnl: float) -> None:
        """Update daily P&L and check if halt should be triggered."""
        self._daily_pnl += pnl
        if self._daily_pnl <= -self.max_daily_loss and not self._halted:
            self._halted = True
            self._halt_reason = HaltReason.DAILY_LOSS_LIMIT
            logger.warning(f"Trading halted: daily loss limit reached ({self._daily_pnl:.2f})")

    def reset_daily(self) -> None:
        """Reset daily counters (call at midnight)."""
        self._daily_pnl = 0.0
        if self._halted and self._halt_reason == HaltReason.DAILY_LOSS_LIMIT:
            self._halted = False
            self._halt_reason = None

    def check_daily_limit(self) -> bool:
        """Return True if daily loss limit NOT exceeded."""
        return not (self._daily_pnl <= -self.max_daily_loss)

    def check_max_positions(self, open_count: int) -> bool:
        """Return True if under max open positions."""
        return open_count < self.max_open_trades

    def check_cooldown(self, symbol: str) -> bool:
        """Return True if symbol is NOT in cooldown."""
        last = self._last_trade_time.get(symbol, 0.0)
        elapsed = time.time() - last
        return elapsed >= self.trade_cooldown_sec

    def record_trade(self, symbol: str) -> None:
        """Record trade time for cooldown tracking."""
        self._last_trade_time[symbol] = time.time()

    def get_cooldown_remaining(self, symbol: str) -> float:
        """Get remaining cooldown seconds for a symbol."""
        last = self._last_trade_time.get(symbol, 0.0)
        elapsed = time.time() - last
        remaining = self.trade_cooldown_sec - elapsed
        return max(0.0, remaining)

    def get_risk_state(self, open_count: int) -> RiskState:
        """Get current risk assessment state."""
        return RiskState(
            is_halted=self._halted,
            halt_reason=self._halt_reason,
            daily_pnl=self._daily_pnl,
            daily_loss_limit=self.max_daily_loss,
            open_positions=open_count,
            max_positions=self.max_open_trades,
            last_trade_time=None,
            cooldown_remaining_sec=self.get_cooldown_remaining(''),
        )

    def manual_halt(self, reason: str = 'manual') -> None:
        """Manually halt trading."""
        self._halted = True
        self._halt_reason = HaltReason.MANUAL
        logger.warning(f"Trading manually halted: {reason}")

    def resume_trading(self) -> None:
        """Resume trading after manual halt."""
        self._halted = False
        self._halt_reason = None
        logger.info("Trading resumed")

    def can_trade(self, symbol: str, open_count: int) -> tuple:
        """
        Check all risk conditions. Returns (can_trade: bool, reason: Optional[str]).
        """
        if self._halted:
            return False, f"Halted: {self._halt_reason.value}"
        if not self.check_daily_limit():
            return False, "Daily loss limit reached"
        if not self.check_max_positions(open_count):
            return False, f"Max positions ({self.max_open_trades}) reached"
        if not self.check_cooldown(symbol):
            remaining = self.get_cooldown_remaining(symbol)
            return False, f"Cooldown active ({remaining:.0f}s)"
        return True, None
