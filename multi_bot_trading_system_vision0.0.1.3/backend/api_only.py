"""Multi-Bot Trading System - API only mode (no frontend).

Usage:
    venv/Scripts/python.exe -m backend.api_only

Serves only the /api/* endpoints on port 5000.
WebSocket provides live price updates in background.
No Angular build required.
"""

import logging
import os
import sys
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend import config
from backend.services.indicators_service import IndicatorService
from backend.services.price_service import PriceService
from backend.News_card.news_service import collect_news, get_news_items

# --- Logging ---------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# --- App -------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'trading_system_secret_key')

CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000",
                   "http://localhost:4200", "http://127.0.0.1:4200"])

# --- Services --------------------------------------------------------------

price_service = PriceService()
indicators_service = IndicatorService()

# Start WebSocket price stream immediately
PriceService.start()

# --- Constants ----------------------------------------------------------------

SUPPORTED_COINS = [
    'BTC', 'ETH', 'SOL', 'ADA', 'BNB',
    'XRP', 'LTC', 'DOT', 'DOGE', 'AVAX',
]


# --- Routes ----------------------------------------------------------------

@app.route('/api/price')
def api_price():
    """Get live price for a coin (instant from cache)."""
    coin = request.args.get('coin', '').strip()
    if not coin:
        return jsonify({"error": "Missing coin parameter", "data": None}), 400

    result = price_service.get_price_sync(coin)
    if result is None or 'error' in result:
        return jsonify({"error": "Coin not found", "data": None}), 404

    return jsonify(result)


@app.route('/api/coins')
def api_coins():
    """Return the list of supported coins."""
    return jsonify(SUPPORTED_COINS)


@app.route('/api/indicators')
def api_indicators():
    """Get technical indicators (RSI, MACD, EMA)."""
    coin = request.args.get("coin", "").strip()
    if not coin:
        return jsonify({"error": "Coin parameter is required", "data": None}), 400

    tf = request.args.get("tf", "1h").strip()
    if tf not in config.TIMEFRAMES:
        tf = "1h"

    result = indicators_service.get_indicators(coin, tf)
    if result is None:
        return jsonify({"error": "Coin not found", "data": None}), 404

    return jsonify(result)


@app.route('/api/status')
def api_status():
    """API health check."""
    return jsonify({
        'mode': 'api-only',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
    })


@app.route('/api/news')
def api_news():
    """Get latest news from configured sources."""
    try:
        result = collect_news()
        items = get_news_items()
        return jsonify({
            "success": True,
            "total_new": result.get("total_new", 0),
            "total_items": len(items),
            "items": items[:50],
        })
    except Exception as e:
        logger.error(f"Error collecting news: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "total_new": 0,
            "total_items": 0,
            "items": [],
        }), 500


@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Get or update current symbol/timeframe settings."""
    if request.method == 'POST':
        data = request.json or {}
        return jsonify({'success': True, **data})
    return jsonify({'symbol': 'BTCUSDT', 'timeframe': '1h'})


@app.route('/api/wallet')
def api_wallet():
    """Get Binance Spot wallet balances."""
    from backend.services.wallet_service import WalletService
    try:
        wallet_service = WalletService()
        result = wallet_service.get_wallet_sync()
        if result is None or 'error' in result:
            return jsonify({"error": "Could not fetch wallet", "data": None}), 500
        return jsonify(result)
    except ValueError as e:
        # API keys not configured
        return jsonify({"error": str(e), "data": None}), 401
    except Exception as e:
        return jsonify({"error": "Wallet service error", "data": None}), 500


@app.route('/api/trades')
def api_get_trades():
    """Get trades history."""
    from backend.app import _load_trades
    trades = _load_trades()
    return jsonify(trades)


@app.route('/')
def root():
    return jsonify({
        'service': 'Multi-Bot Trading System (API only)',
        'endpoints': {
            'GET /api/price?coin=xxx': 'Live price (WebSocket cached)',
            'GET /api/indicators?coin=xxx&tf=1h': 'Technical indicators (RSI, MACD, EMA)',
            'GET /api/news': 'Latest news from configured sources',
            'GET /api/status': 'Health check',
            'GET/POST /api/settings': 'Settings',
        },
    })


# --- Main ------------------------------------------------------------------

if __name__ == '__main__':
    logger.info("Starting API-only server (WebSocket price feed)…")
    try:
        app.run(debug=False, host='127.0.0.1', port=config.DASHBOARD_PORT, use_reloader=False)
    finally:
        PriceService.stop()
