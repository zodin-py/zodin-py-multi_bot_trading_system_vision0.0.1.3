"""Position sizing — calculate trade quantity based on risk parameters."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PositionSizer:
    """Calculates position size based on risk percentage and stop loss distance."""

    def __init__(
        self,
        risk_percent: float = 1.0,
        risk_reward_ratio: float = 2.0,
        max_open_trades: int = 5,
    ):
        self.risk_percent = risk_percent
        self.risk_reward_ratio = risk_reward_ratio
        self.max_open_trades = max_open_trades

    def calculate_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
    ) -> float:
        """
        Calculate position size.

        Formula: size = (capital * risk_percent) / (entry_price - stop_loss)
        """
        if entry_price <= 0 or stop_loss <= 0:
            return 0.0

        risk_amount = capital * (self.risk_percent / 100.0)
        risk_per_unit = abs(entry_price - stop_loss)

        if risk_per_unit <= 0:
            return 0.0

        size = risk_amount / risk_per_unit
        return max(size, 0.0)

    def can_open_trade(self, open_count: int) -> bool:
        """Check if we can open a new trade (within max limit)."""
        return open_count < self.max_open_trades
