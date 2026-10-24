# filepath: config.py
"""
Konfigurationsdatei für das Multi-Bot Trading System
verwaltet alle Umgebungsvariablen und Konfiguration über Pydantic BaseSettings.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TradingConfig(BaseSettings):
    """Core trading configuration with type validation and lazy getters."""

    # ==================== BINANCE API KONFIGURATION ====================
    BINANCE_API_KEY: str = Field(default='', description='Binance API Key')
    BINANCE_SECRET_KEY: str = Field(default='', description='Binance Secret Key')

    USE_TESTNET: bool = Field(default=True, description='Use Binance Testnet')

    # ==================== CCXT / DATENLAYER ====================
    CCXT_RATE_LIMIT: int = Field(default=1000, description='Base interval in ms for ccxt rate limiting')

    DUCKDB_PATH: str = Field(
        default='.data/cache.duckdb',
        description='Path to DuckDB cache file'
    )

    CACHE_TTL_SEC: int = Field(default=300, description='Cache TTL in seconds')

    # ==================== TRADING KONFIGURATION ====================
    COINS: List[str] = Field(
        default=[
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
            'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'KITEUSDT',
            'LINKUSDT', 'LTCUSDT', 'UNIUSDT', 'ATOMUSDT', 'ETCUSDT'
        ],
        description='List of trading symbols'
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

    # ==================== RISK MANAGEMENT ====================
    RISK_PERCENT: float = Field(default=1.0, description='Risk percent per trade')
    RISK_REWARD_RATIO: float = Field(default=2.0, description='Risk-reward ratio')
    MAX_OPEN_TRADES: int = Field(default=5, description='Maximum open trades')

    MAX_DAILY_LOSS: float = Field(default=10.0, description='Maximum daily loss limit')

    TRADE_COOLDOWN_SEC: int = Field(default=60, description='Trade cooldown in seconds')

    DYNAMIC_SL_TP_ENABLED: bool = Field(
        default=True,
        description='Enable dynamic SL/TP from support/resistance'
    )

    # ==================== SERVER / PORTS ====================
    API_PORT: int = Field(default=8000, description='FastAPI REST server port')
    MCP_PORT: int = Field(default=8001, description='MCP server port')
    DASHBOARD_PORT: int = Field(default=5000, description='Flask dashboard port')

    # ==================== BOT KONFIGURATION ====================
    BOT_WEIGHTS: Dict[str, float] = Field(
        default={
            'rsi': 0.15,
            'macd': 0.15,
            'mfi': 0.10,
            'sr': 0.15,
            'smc': 0.15,
            'harmonic': 0.10,
            'trend': 0.20
        },
        description='Bot weight configuration'
    )

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
            'mfi': {
                'period': 14,
                'overbought': 80,
                'oversold': 20,
                'weight': 0.10
            },
            'adx': {
                'period': 14,
                'trend_threshold': 25
            }
        },
        description='Indicator parameters configuration'
    )

    # ==================== SIGNAL SCHWELLEN ====================
    SIGNAL_THRESHOLDS: Dict[str, int] = Field(
        default={
            'min_buy_probability': 65,
            'min_sell_probability': 65,
            'min_confidence': 60
        },
        description='Signal thresholds'
    )

    # ==================== PERSISTENZ ====================
    TRADES_HISTORY_FILE: str = Field(
        default='trades/trades_history.json',
        description='Trades history file path'
    )
    LOG_FILE: str = Field(
        default='trades/trading.log',
        description='Log file path'
    )

    # ==================== UI KONFIGURATION ====================
    REFRESH_INTERVAL: int = Field(default=5, description='Refresh interval in seconds')

    # ==================== BACKTESTING ====================
    BACKTEST_MODE: bool = Field(default=False, description='Backtesting mode')
    INITIAL_CAPITAL: float = Field(default=10000, description='Initial capital for backtesting')

    # ==================== INDIVIDUAL CONFIG FIELDS FOR LAZY GETTERS ====================
    # Bot weights as individual fields
    BOT_RSI: float = Field(default=0.15, description='RSI bot weight')
    BOT_MACD: float = Field(default=0.15, description='MACD bot weight')
    BOT_MFI: float = Field(default=0.10, description='MFI bot weight')
    BOT_SR: float = Field(default=0.15, description='SR bot weight')
    BOT_SMC: float = Field(default=0.15, description='SMC bot weight')
    BOT_HARMONIC: float = Field(default=0.10, description='Harmonic bot weight')
    BOT_TREND: float = Field(default=0.20, description='Trend bot weight')

    # Indicator params as individual fields
    IND_RSI_PERIOD: int = Field(default=14, description='RSI period')
    IND_RSI_OVERBOUGHT: int = Field(default=70, description='RSI overbought threshold')
    IND_RSI_OVERSOLD: int = Field(default=30, description='RSI oversold threshold')
    IND_MACD_FAST: int = Field(default=12, description='MACD fast period')
    IND_MACD_SLOW: int = Field(default=26, description='MACD slow period')
    IND_MACD_SIGNAL: int = Field(default=9, description='MACD signal period')
    IND_ADX_PERIOD: int = Field(default=14, description='ADX period')
    IND_ADX_TREND_THRESHOLD: int = Field(default=25, description='ADX trend threshold')

    # Risk config as individual fields
    RISK_MAX_DAILY_LOSS: float = Field(default=10.0, description='Max daily loss')
    RISK_TRADE_COOLDOWN_SEC: int = Field(default=60, description='Trade cooldown seconds')
    RISK_MAX_OPEN_TRADES: int = Field(default=5, description='Max open trades')
    RISK_RISK_PERCENT: float = Field(default=1.0, description='Risk percent')
    RISK_RISK_REWARD_RATIO: float = Field(default=2.0, description='Risk reward ratio')

    # Signal config as individual fields
    SIG_MIN_BUY_PROBABILITY: float = Field(default=65.0, description='Min buy probability')
    SIG_MIN_SELL_PROBABILITY: float = Field(default=65.0, description='Min sell probability')
    SIG_MIN_CONFIDENCE: float = Field(default=60.0, description='Min confidence')

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
DUCKDB_PATH: str = config.DUCKDB_PATH
CACHE_TTL_SEC: int = config.CACHE_TTL_SEC
RISK_PERCENT: float = config.RISK_PERCENT
RISK_REWARD_RATIO: float = config.RISK_REWARD_RATIO
MAX_OPEN_TRADES: int = config.MAX_OPEN_TRADES
MAX_DAILY_LOSS: float = config.MAX_DAILY_LOSS
TRADE_COOLDOWN_SEC: int = config.TRADE_COOLDOWN_SEC
DYNAMIC_SL_TP_ENABLED: bool = config.DYNAMIC_SL_TP_ENABLED
API_PORT: int = config.API_PORT
MCP_PORT: int = config.MCP_PORT
DASHBOARD_PORT: int = config.DASHBOARD_PORT
BOT_WEIGHTS: Dict[str, float] = config.BOT_WEIGHTS
INDICATOR_PARAMS: Dict[str, Any] = config.INDICATOR_PARAMS
SIGNAL_THRESHOLDS: Dict[str, int] = config.SIGNAL_THRESHOLDS
TRADES_HISTORY_FILE: str = config.TRADES_HISTORY_FILE
LOG_FILE: str = config.LOG_FILE
REFRESH_INTERVAL: int = config.REFRESH_INTERVAL
BACKTEST_MODE: bool = config.BACKTEST_MODE
INITIAL_CAPITAL: float = config.INITIAL_CAPITAL
COINS: List[str] = config.COINS
TIMEFRAMES: Dict[str, str] = config.TIMEFRAMES


# ==================== LAZY CONFIG GETTERS ====================
# These return lightweight dataclass-like objects with only the relevant fields

class BotConfig:
    """Lightweight bot weight config."""
    def __init__(self, cfg: TradingConfig):
        self.rsi = cfg.BOT_RSI
        self.macd = cfg.BOT_MACD
        self.mfi = cfg.BOT_MFI
        self.sr = cfg.BOT_SR
        self.smc = cfg.BOT_SMC
        self.harmonic = cfg.BOT_HARMONIC
        self.trend = cfg.BOT_TREND

    def to_dict(self) -> dict:
        return {
            'rsi': self.rsi, 'macd': self.macd, 'mfi': self.mfi,
            'sr': self.sr, 'smc': self.smc, 'harmonic': self.harmonic,
            'trend': self.trend
        }


class IndicatorConfig:
    """Lightweight indicator param config."""
    def __init__(self, cfg: TradingConfig):
        self.rsi_period = cfg.IND_RSI_PERIOD
        self.rsi_overbought = cfg.IND_RSI_OVERBOUGHT
        self.rsi_oversold = cfg.IND_RSI_OVERSOLD
        self.macd_fast = cfg.IND_MACD_FAST
        self.macd_slow = cfg.IND_MACD_SLOW
        self.macd_signal = cfg.IND_MACD_SIGNAL
        self.adx_period = cfg.IND_ADX_PERIOD
        self.adx_trend_threshold = cfg.IND_ADX_TREND_THRESHOLD

    def to_dict(self) -> dict:
        return {
            'rsi_period': self.rsi_period, 'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold, 'macd_fast': self.macd_fast,
            'macd_slow': self.macd_slow, 'macd_signal': self.macd_signal,
            'adx_period': self.adx_period, 'adx_trend_threshold': self.adx_trend_threshold
        }


class RiskConfig:
    """Lightweight risk config."""
    def __init__(self, cfg: TradingConfig):
        self.max_daily_loss = cfg.RISK_MAX_DAILY_LOSS
        self.trade_cooldown_sec = cfg.RISK_TRADE_COOLDOWN_SEC
        self.max_open_trades = cfg.RISK_MAX_OPEN_TRADES
        self.risk_percent = cfg.RISK_RISK_PERCENT
        self.risk_reward_ratio = cfg.RISK_RISK_REWARD_RATIO

    def to_dict(self) -> dict:
        return {
            'max_daily_loss': self.max_daily_loss,
            'trade_cooldown_sec': self.trade_cooldown_sec,
            'max_open_trades': self.max_open_trades,
            'risk_percent': self.risk_percent,
            'risk_reward_ratio': self.risk_reward_ratio
        }


class SignalConfig:
    """Lightweight signal threshold config."""
    def __init__(self, cfg: TradingConfig):
        self.min_buy_probability = cfg.SIG_MIN_BUY_PROBABILITY
        self.min_sell_probability = cfg.SIG_MIN_SELL_PROBABILITY
        self.min_confidence = cfg.SIG_MIN_CONFIDENCE

    def to_dict(self) -> dict:
        return {
            'min_buy_probability': self.min_buy_probability,
            'min_sell_probability': self.min_sell_probability,
            'min_confidence': self.min_confidence
        }


# Lazy-initialized config instances
_bot_config: BotConfig | None = None
_indicator_config: IndicatorConfig | None = None
_risk_config: RiskConfig | None = None
_signal_config: SignalConfig | None = None


def get_bot_config() -> BotConfig:
    global _bot_config
    if _bot_config is None:
        _bot_config = BotConfig(TradingConfig())
    return _bot_config


def get_indicator_config() -> IndicatorConfig:
    global _indicator_config
    if _indicator_config is None:
        _indicator_config = IndicatorConfig(TradingConfig())
    return _indicator_config


def get_risk_config() -> RiskConfig:
    global _risk_config
    if _risk_config is None:
        _risk_config = RiskConfig(TradingConfig())
    return _risk_config


def get_signal_config() -> SignalConfig:
    global _signal_config
    if _signal_config is None:
        _signal_config = SignalConfig(TradingConfig())
    return _signal_config


__all__ = [
    'TradingConfig',
    'config',
    'get_base_url',
    'get_ws_url',
    'get_bot_config',
    'get_indicator_config',
    'get_risk_config',
    'get_signal_config',
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
    'MCP_PORT',
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