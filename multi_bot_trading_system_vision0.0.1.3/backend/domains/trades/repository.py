"""Trades repository.

Manages persistence of trade records.
"""

from backend.domains.execution.repository import TradeRepository as TradesRepository

__all__ = ["TradesRepository"]