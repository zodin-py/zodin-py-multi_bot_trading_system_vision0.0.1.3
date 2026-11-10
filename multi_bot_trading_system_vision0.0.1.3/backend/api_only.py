"""Multi-Bot Trading System - Flask API and Angular dashboard.

Usage:
    venv/Scripts/python.exe -m backend.api_only

Serves the Angular build and /api/* endpoints on port 5000.
The Angular application must be built before starting the server.
WebSocket provides live price updates in background.
"""

import json
import logging
import os
import sys
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ccxt.base.errors import AuthenticationError
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import safe_join

from backend import config
from backend.services.indicators_service import IndicatorService
from backend.services.price_service import PriceService
from backend.News_card.news_service import collect_news, get_news_items
from backend.candles.manager import load_candles, update_candle_data

# --- Logging ---------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# --- App -------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'trading_system_secret_key')
ANGULAR_DIST = os.path.join(
    PROJECT_ROOT, 'frontend', 'angular', 'dist', 'angular', 'browser'
)
TRADES_HISTORY_FILE = os.path.abspath(
    os.path.join(PROJECT_ROOT, '..', 'trades', 'trades_history.json')
)

CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000",
                   "http://localhost:4200", "http://127.0.0.1:4200"])

# --- Services --------------------------------------------------------------

price_service = PriceService()
indicators_service = IndicatorService()

# Start WebSocket price stream immediately
PriceService.start()

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
    """Return supported coins and candle timeframes."""
    return jsonify({
        'success': True,
        'coins': config.COINS,
        'timeframes': config.TIMEFRAMES,
    })


@app.route('/api/coins/<symbol>/candles')
def api_coin_candles(symbol: str):
    """Get stored candle data for a supported symbol and timeframe."""
    timeframe = request.args.get('timeframe', '5m').strip()
    if timeframe not in config.TIMEFRAMES:
        timeframe = '5m'

    try:
        limit = max(1, min(int(request.args.get('limit', 100)), 1000))
    except (ValueError, TypeError):
        limit = 100

    if symbol not in config.COINS:
        return jsonify({
            'success': False,
            'error': f"Symbol '{symbol}' not in supported coins list",
        }), 400

    candle_data, success = load_candles(symbol, timeframe)
    if not success or not candle_data:
        return jsonify({
            'success': False,
            'error': 'No candle data available',
            'candles': [],
            'candle_count': 0,
        }), 404

    candles = candle_data.get('candles', [])
    return jsonify({
        'success': True,
        'symbol': symbol,
        'timeframe': timeframe,
        'candles': candles[-limit:],
        'candle_count': len(candles),
        'returned_count': min(len(candles), limit),
    })


@app.route('/api/coins/<symbol>/select', methods=['POST'])
def api_coin_select(symbol: str):
    """Fetch and persist candle data for a supported symbol/timeframe."""
    data = request.get_json(silent=True) or {}
    timeframe = data.get('timeframe', '5m')
    if timeframe not in config.TIMEFRAMES:
        timeframe = '5m'

    if symbol not in config.COINS:
        return jsonify({
            'success': False,
            'error': f"Symbol '{symbol}' not in supported coins list",
        }), 400

    update_summary = update_candle_data(symbol, timeframe)
    if not update_summary['success']:
        return jsonify({
            'success': False,
            'error': update_summary.get('error', 'Failed to update candle data'),
        }), 500

    return jsonify({
        'success': True,
        'symbol': symbol,
        'timeframe': timeframe,
        'candles_loaded': update_summary['candles_loaded'],
        'new_candles': update_summary['new_candles'],
        'duplicates_skipped': update_summary['duplicates_skipped'],
        'message': f'Candle data updated for {symbol}/{timeframe}',
    })


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
            return jsonify({"error": "Could not fetch wallet", "data": None}), 502
        return jsonify(result)
    except ValueError as e:
        # API keys not configured
        return jsonify({"error": str(e), "data": None}), 401
    except AuthenticationError:
        logger.warning("Binance rejected wallet credentials or permissions")
        return jsonify({
            "error": "Binance API key, IP allow-list, or permissions are invalid",
            "data": None,
        }), 401
    except Exception as e:
        logger.error("Wallet service error: %s", type(e).__name__)
        return jsonify({"error": "Wallet service error", "data": None}), 502


@app.route('/api/trades')
def api_get_trades():
    """Get trades history."""
    try:
        with open(TRADES_HISTORY_FILE, 'r', encoding='utf-8') as trades_file:
            trades = json.load(trades_file)
    except FileNotFoundError:
        trades = []
    except json.JSONDecodeError:
        logger.exception("Invalid trades history JSON in %s", TRADES_HISTORY_FILE)
        return jsonify({'error': 'Trade history contains invalid JSON'}), 500
    except OSError:
        logger.exception("Could not read trades history from %s", TRADES_HISTORY_FILE)
        return jsonify({'error': 'Trade history could not be read'}), 500

    if not isinstance(trades, list):
        logger.error("Trades history in %s must contain a JSON list", TRADES_HISTORY_FILE)
        return jsonify({'error': 'Trade history must contain a JSON list'}), 500

    limit_value = request.args.get('limit')
    if limit_value is not None:
        try:
            limit = int(limit_value)
            if limit < 1:
                raise ValueError
        except ValueError:
            return jsonify({'error': 'limit must be a positive integer'}), 400
        trades = trades[-min(limit, 1000):]

    return jsonify(trades)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_angular(path: str):
    """Serve the built Angular dashboard and route browser paths to its SPA."""
    if path == 'api' or path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404

    index_file = os.path.join(ANGULAR_DIST, 'index.html')
    if not os.path.isfile(index_file):
        return jsonify({
            'error': (
                'Angular build not found. Run npm install and npm run build '
                'in frontend/angular.'
            )
        }), 503

    requested_file = safe_join(ANGULAR_DIST, path) if path else None
    if requested_file and os.path.isfile(requested_file):
        return send_from_directory(ANGULAR_DIST, path)
    return send_from_directory(ANGULAR_DIST, 'index.html')


# --- Main ------------------------------------------------------------------

if __name__ == '__main__':
    logger.info("Starting API-only server (WebSocket price feed)…")
    try:
        app.run(debug=False, host='127.0.0.1', port=config.DASHBOARD_PORT, use_reloader=False)
    finally:
        PriceService.stop()
