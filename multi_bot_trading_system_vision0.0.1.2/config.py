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