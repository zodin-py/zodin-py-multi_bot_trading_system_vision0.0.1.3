# filepath: config.py
"""Konfigurationsdatei für das Multi-Bot Trading System

Nur die für Preis, Wallet und Indikatoren benötigten Felder sind enthalten.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingConfig(BaseSettings):
    """Core trading configuration — reduced to minimum for price, wallet, indicators.

    Removed fields (for reference only):
    - BOT_WEIGHTS, RISK_PERCENT, RISK_REWARD_RATIO, MAX_OPEN_TRADES
    - MAX_DAILY_LOSS, TRADE_COOLDOWN_SEC, DYNAMIC_SL_TP_ENABLED
    - INDICATOR_PARAMS weight keys, ADX params
    - SIGNAL_THRESHOLDS
    - TRADES_HISTORY_FILE, LOG_FILE, REFRESH_INTERVAL
    - BACKTEST_MODE, INITIAL_CAPITAL
    - Individual bot weight / indicator param fields
    """

    # ==================== BINANCE API KONFIGURATION ====================
    BINANCE_API_KEY: str = Field(default='', repr=False, description='Binance API Key')
    BINANCE_SECRET_KEY: str = Field(default='', repr=False, description='Binance Secret Key')

    USE_TESTNET: bool = Field(default=True, description='Use Binance Testnet')

    # ==================== CCXT / DATENLAYER ====================
    CCXT_RATE_LIMIT: int = Field(default=1000, description='Base interval in ms for ccxt rate limiting')

    # ==================== TRADING KONFIGURATION ====================
    # Minimal coin list for lookup validation
    COINS: List[str] = Field(
        default=[
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT',
        ],
        description='List of supported trading symbols'
    )

    TIMEFRAMES: Dict[str, str] = Field(
        default={
            '1m': '1 Minute',
            '5m': '5 Minutes',
            '15m': '15 Minutes',
            '1h': '1 Hour',
            '4h': '4 Hours',
            '1d': '1 Day'
        },
        description='Mapping of timeframes'
    )

    # ==================== SERVER / PORTS ====================
    API_PORT: int = Field(default=8000, description='FastAPI REST server port')
    DASHBOARD_PORT: int = Field(default=5000, description='Flask dashboard port')

    # ==================== INDICATOR PARAMETERS ====================
    INDICATOR_PARAMS: Dict[str, Any] = Field(
        default={
            'rsi': {
                'period': 14,
                'overbought': 70,
                'oversold': 30,
                'weight': 0.15
            },
            'macd': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'weight': 0.15
            },
            'ema': {
                'period': 20,
                'weight': 0.15
            }
        },
        description='Indicator parameters configuration for price/wallet/indicators'
    )

    # ==================== DEFAULT QUOTE ====================
    DEFAULT_QUOTE: str = Field(default='USDT', description='Default quote currency')

    # --- Backward-compatible module-level exports ---
    # (exposed at bottom of file)

    model_config = SettingsConfigDict(
        env_prefix='TRADING_',
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


# --- Backward-compatible module-level exports ---

# --- Lazy getter / computed properties ---

def get_base_url() -> str:
    """Dynamically compute BASE_URL from USE_TESTNET setting."""
    cfg = TradingConfig()
    return 'https://testnet.binance.vision' if cfg.USE_TESTNET else 'https://api.binance.com'


def get_ws_url() -> str:
    """Dynamically compute WS_URL from USE_TESTNET setting."""
    cfg = TradingConfig()
    return 'wss://stream.testnet.binance.vision:9443/ws' if cfg.USE_TESTNET else 'wss://stream.binance.com:9443/ws'


# --- Backward-compatible module-level exports ---

# The central config instance - all imports should use `from backend.config import config`
# and access values via config.X or the convenience exports below.
config = TradingConfig()

# Export individual values for backward compatibility with existing code that does
# `from backend.config import BINANCE_API_KEY`, `from backend.config import MAX_DAILY_LOSS`, etc.
# These read from the TradingConfig instance at import time.
BINANCE_API_KEY: str = config.BINANCE_API_KEY
BINANCE_SECRET_KEY: str = config.BINANCE_SECRET_KEY
USE_TESTNET: bool = config.USE_TESTNET
BASE_URL: str = get_base_url()
WS_URL: str = get_ws_url()
CCXT_RATE_LIMIT: int = config.CCXT_RATE_LIMIT
DUCKDB_PATH: str = config.DUCKDB_PATH if hasattr(config, 'DUCKDB_PATH') else '.data/cache.duckdb'
CACHE_TTL_SEC: int = config.CACHE_TTL_SEC if hasattr(config, 'CACHE_TTL_SEC') else 300
RISK_PERCENT: float = config.RISK_PERCENT if hasattr(config, 'RISK_PERCENT') else 1.0
RISK_REWARD_RATIO: float = config.RISK_REWARD_RATIO if hasattr(config, 'RISK_REWARD_RATIO') else 2.0
MAX_OPEN_TRADES: int = config.MAX_OPEN_TRADES if hasattr(config, 'MAX_OPEN_TRADES') else 5
MAX_DAILY_LOSS: float = config.MAX_DAILY_LOSS if hasattr(config, 'MAX_DAILY_LOSS') else 10.0
TRADE_COOLDOWN_SEC: int = config.TRADE_COOLDOWN_SEC if hasattr(config, 'TRADE_COOLDOWN_SEC') else 60
DYNAMIC_SL_TP_ENABLED: bool = config.DYNAMIC_SL_TP_ENABLED if hasattr(config, 'DYNAMIC_SL_TP_ENABLED') else True
API_PORT: int = config.API_PORT
DASHBOARD_PORT: int = config.DASHBOARD_PORT
BOT_WEIGHTS: Dict[str, float] = config.BOT_WEIGHTS if hasattr(config, 'BOT_WEIGHTS') else {}
INDICATOR_PARAMS: Dict[str, Any] = config.INDICATOR_PARAMS
SIGNAL_THRESHOLDS: Dict[str, int] = config.SIGNAL_THRESHOLDS if hasattr(config, 'SIGNAL_THRESHOLDS') else {}
TRADES_HISTORY_FILE: str = config.TRADES_HISTORY_FILE if hasattr(config, 'TRADES_HISTORY_FILE') else 'trades/trades_history.json'
LOG_FILE: str = config.LOG_FILE if hasattr(config, 'LOG_FILE') else 'trades/trading.log'
REFRESH_INTERVAL: int = config.REFRESH_INTERVAL if hasattr(config, 'REFRESH_INTERVAL') else 5
BACKTEST_MODE: bool = config.BACKTEST_MODE if hasattr(config, 'BACKTEST_MODE') else False
INITIAL_CAPITAL: float = config.INITIAL_CAPITAL if hasattr(config, 'INITIAL_CAPITAL') else 10000.0
COINS: List[str] = config.COINS
TIMEFRAMES: Dict[str, str] = config.TIMEFRAMES
DEFAULT_QUOTE: str = config.DEFAULT_QUOTE


__all__ = [
    'TradingConfig',
    'config',
    'get_base_url',
    'get_ws_url',
    # backward-compatible flat exports
    'BINANCE_API_KEY',
    'BINANCE_SECRET_KEY',
    'USE_TESTNET',
    'BASE_URL',
    'WS_URL',
    'CCXT_RATE_LIMIT',
    'DUCKDB_PATH',
    'CACHE_TTL_SEC',
    'RISK_PERCENT',
    'RISK_REWARD_RATIO',
    'MAX_OPEN_TRADES',
    'MAX_DAILY_LOSS',
    'TRADE_COOLDOWN_SEC',
    'DYNAMIC_SL_TP_ENABLED',
    'API_PORT',
    'DASHBOARD_PORT',
    'BOT_WEIGHTS',
    'INDICATOR_PARAMS',
    'SIGNAL_THRESHOLDS',
    'TRADES_HISTORY_FILE',
    'LOG_FILE',
    'REFRESH_INTERVAL',
    'BACKTEST_MODE',
    'INITIAL_CAPITAL',
    'COINS',
    'TIMEFRAMES',
]