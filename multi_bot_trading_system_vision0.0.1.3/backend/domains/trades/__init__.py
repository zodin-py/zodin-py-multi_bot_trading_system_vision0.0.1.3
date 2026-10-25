"""Trades domain package.

Manages trade records, history, and trade-related operations.
"""

from .models import Trade, TradeStatus, TradeType
from .repository import TradesRepository
from .service import TradesService

__all__ = [
    "Trade",
    "TradeStatus",
    "TradeType",
    "TradesRepository",
    "TradesService",
]