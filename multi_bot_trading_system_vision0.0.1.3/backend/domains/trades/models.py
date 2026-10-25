"""Trades domain models.

Defines data structures for trades, fills, and trade history.
"""

from typing import Literal, TypeAlias

from backend.domains.execution.models import Trade, TradeStatus

TradeType: TypeAlias = Literal["long", "short"]

__all__ = ["Trade", "TradeStatus", "TradeType"]