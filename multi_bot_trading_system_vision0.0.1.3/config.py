# filepath: config.py
"""
Konfigurationsdatei für das Multi-Bot Trading System
"""

import os
from datetime import datetime

# ==================== BINANCE API KONFIGURATION ====================
BINANCE_API_KEY = os.environ.get('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY', '')

# Testnet für Paper Trading
USE_TESTNET = True
BASE_URL = 'https://testnet.binance.vision' if USE_TESTNET else 'https://api.binance.com'
WS_URL = 'wss://stream.testnet.binance.vision:9443/ws' if USE_TESTNET else 'wss://stream.binance.com:9443/ws'

# ==================== CCXT / DATENLAYER ====================
# ccxt behandelt Rate-Limits intern; this is the base interval in ms
CCXT_RATE_LIMIT = int(os.environ.get('CCXT_RATE_LIMIT', '1000'))

# Persistenter DuckDB-Cache für Kerzen & Indikatoren
DUCKDB_PATH = os.environ.get('DUCKDB_PATH', os.path.join('.data', 'cache.duckdb'))

# TTL (Sekunden) für gecachte Kerzen; ältere Daten werden verworfen/erneuert
CACHE_TTL_SEC = int(os.environ.get('CACHE_TTL_SEC', '300'))

# ==================== TRADING KONFIGURATION ====================
COINS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'KITEUSDT',
    'LINKUSDT', 'LTCUSDT', 'UNIUSDT', 'ATOMUSDT', 'ETCUSDT'
]

TIMEFRAMES = {
    '1m': '1 Minute',
    '5m': '5 Minutes',
    '15m': '15 Minutes',
    '1h': '1 Hour',
    '4h': '4 Hours',
    '1d': '1 Day'
}

# ==================== RISK MANAGEMENT ====================
RISK_PERCENT = 1.0
RISK_REWARD_RATIO = 2.0
MAX_OPEN_TRADES = 5

# Konfigurierbares tägliches Verlustlimit (in Account-Whährung, z.B. EUR/USDT)
# Trading wird automatisch gestoppt (TRADING_HALTED), wenn daily_pnl <= -MAX_DAILY_LOSS
MAX_DAILY_LOSS = float(os.environ.get('MAX_DAILY_LOSS', '10.0'))

# Cooldown zwischen Trades pro Symbol in Sekunden
TRADE_COOLDOWN_SEC = int(os.environ.get('TRADE_COOLDOWN_SEC', '60'))

# Dynamische TR/TP-Berechnung aus Support/Resistance (Fallback: statisch/ATR)
DYNAMIC_SL_TP_ENABLED = os.environ.get('DYNAMIC_SL_TP_ENABLED', 'true').lower() == 'true'

# ==================== SERVER / PORTS ====================
API_PORT = int(os.environ.get('API_PORT', '8000'))        # FastAPI REST
MCP_PORT = int(os.environ.get('MCP_PORT', '8001'))        # MCP (falls HTTP-Modus)
DASHBOARD_PORT = int(os.environ.get('DASHBOARD_PORT', '5000'))  # Flask Dashboard

# ==================== BOT KONFIGURATION ====================
BOT_WEIGHTS = {
    'rsi': 0.15,
    'macd': 0.15,
    'mfi': 0.10,
    'sr': 0.15,
    'smc': 0.15,
    'harmonic': 0.10,
    'trend': 0.20
}

INDICATOR_PARAMS = {
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
}

# ==================== SIGNAL SCHWELLEN ====================
SIGNAL_THRESHOLDS = {
    'min_buy_probability': 65,
    'min_sell_probability': 65,
    'min_confidence': 60
}

# ==================== PERSISTENZ ====================
TRADES_HISTORY_FILE = 'trades/trades_history.json'
LOG_FILE = 'trades/trading.log'

# ==================== UI KONFIGURATION ====================
REFRESH_INTERVAL = 5

# ==================== BACKTESTING ====================
BACKTEST_MODE = False
INITIAL_CAPITAL = 10000