"""Backend package for Multi-Bot Trading System."""

# Re-export config for backwards compatibility
from .config import (
    BINANCE_API_KEY,
    BINANCE_SECRET_KEY,
    USE_TESTNET,
    CCXT_RATE_LIMIT,
    COINS,
    TIMEFRAMES,
    API_PORT,
    DASHBOARD_PORT,
    INDICATOR_PARAMS,
    DEFAULT_QUOTE,
)

__all__ = [
    'BINANCE_API_KEY',
    'BINANCE_SECRET_KEY',
    'USE_TESTNET',
    'CCXT_RATE_LIMIT',
    'COINS',
    'TIMEFRAMES',
    'API_PORT',
    'DASHBOARD_PORT',
    'INDICATOR_PARAMS',
    'DEFAULT_QUOTE',
]