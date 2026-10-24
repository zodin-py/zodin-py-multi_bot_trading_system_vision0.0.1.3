"""SL/TP calculator — dynamic stop loss and take profit from SR levels or ATR."""

from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class SLTPCalculator:
    """Calculate dynamic SL/TP based on Support/Resistance or ATR fallback."""

    def __init__(self, risk_reward_ratio: float = 2.0, dynamic_enabled: bool = True):
        self.risk_reward_ratio = risk_reward_ratio
        self.dynamic_enabled = dynamic_enabled

    def calculate(
        self,
        entry_price: float,
        side: str,
        sr_levels: Optional[List[float]] = None,
        atr: float = 0.0,
    ) -> tuple[float, float, str]:
        """
        Calculate stop_loss and take_profit.

        Returns: (stop_loss, take_profit, source)
        source = 'sr_level' or 'atr_fallback'
        """
        if self.dynamic_enabled and sr_levels:
            sl, tp, source = self._calculate_from_sr(entry_price, side, sr_levels)
            if sl and tp:
                return sl, tp, source

        # Fallback to ATR
        if atr > 0:
            return self._calculate_from_atr(entry_price, side, atr)

        # Last resort: static 2%
        return self._calculate_static(entry_price, side)

    def _calculate_from_sr(self, entry_price: float, side: str, levels: List[float]) -> tuple[float, float, str]:
        """Calculate SL/TP from nearest Support/Resistance level."""
        if side == 'long':
            sl_level = self._find_nearest(levels, entry_price, below=True)
            if sl_level is None:
                return 0.0, 0.0, ''
            tp_level = self._find_nearest(levels, entry_price, below=False)
            if tp_level is None:
                return sl_level, entry_price * (1 + self.risk_reward_ratio * 0.02), 'sr_level'
            return sl_level, tp_level, 'sr_level'
        else:  # short
            sl_level = self._find_nearest(levels, entry_price, below=False)
            if sl_level is None:
                return 0.0, 0.0, ''
            tp_level = self._find_nearest(levels, entry_price, below=True)
            if tp_level is None:
                return sl_level, entry_price * (1 - self.risk_reward_ratio * 0.02), 'sr_level'
            return sl_level, tp_level, 'sr_level'

    def _calculate_from_atr(self, entry_price: float, side: str, atr: float) -> tuple[float, float, str]:
        """Calculate SL/TP from ATR."""
        atr_dist = atr * 1.5
        if side == 'long':
            return entry_price - atr_dist, entry_price + atr_dist * self.risk_reward_ratio, 'atr_fallback'
        else:
            return entry_price + atr_dist, entry_price - atr_dist * self.risk_reward_ratio, 'atr_fallback'

    def _calculate_static(self, entry_price: float, side: str) -> tuple[float, float, str]:
        """Static 2% SL/TP."""
        pct = 0.02
        if side == 'long':
            return entry_price * (1 - pct), entry_price * (1 + pct * self.risk_reward_ratio), 'static'
        else:
            return entry_price * (1 + pct), entry_price * (1 - pct * self.risk_reward_ratio), 'static'

    def _find_nearest(self, levels: List[float], price: float, below: bool) -> Optional[float]:
        """Find nearest level below (True) or above (False) price."""
        if not levels:
            return None
        filtered = [l for l in levels if (l < price) == below]
        return max(filtered) if filtered else None
