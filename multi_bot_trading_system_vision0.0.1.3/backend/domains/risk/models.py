"""Risk domain models — RiskState, RiskLimit, HaltReason."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class HaltReason(Enum):
    DAILY_LOSS_LIMIT = 'daily_loss_limit'
    MAX_POSITIONS = 'max_positions'
    COOLDOWN = 'cooldown'
    MANUAL = 'manual'


@dataclass
class RiskLimit:
    """Configurable risk limit."""
    name: str
    value: float
    unit: str = ''
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'enabled': self.enabled,
        }


@dataclass
class RiskState:
    """Current risk assessment state."""
    is_halted: bool
    halt_reason: Optional[HaltReason] = None
    daily_pnl: float = 0.0
    daily_loss_limit: float = 0.0
    open_positions: int = 0
    max_positions: int = 0
    last_trade_time: Optional[datetime] = None
    cooldown_remaining_sec: float = 0.0

    def to_dict(self) -> dict:
        return {
            'is_halted': self.is_halted,
            'halt_reason': self.halt_reason.value if self.halt_reason else None,
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_loss_limit': round(self.daily_loss_limit, 2),
            'open_positions': self.open_positions,
            'max_positions': self.max_positions,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'cooldown_remaining_sec': round(self.cooldown_remaining_sec, 1),
        }
