# filepath: app.py

import json
import logging
import math
import os
import threading
import time
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import safe_join

from backend import config
from backend.services.indicators_service import IndicatorService
from backend.services.price_service import PriceService
from backend.services.wallet_service import WalletService
from backend.config import COINS, TIMEFRAMES, REFRESH_INTERVAL

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask App
# Serve the Angular browser build in production.
angular_dist = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'frontend',
        'angular',
        'dist',
        'angular',
        'browser',
    )
)
app = Flask(__name__, static_folder=None)
app.secret_key = 'trading_system_secret_key'

# CORS for Flask endpoints (dashboard on 5000 calls FastAPI on 8000, but Flask still serves some endpoints)
# Also allow Angular dev server on port 4200
from flask_cors import CORS
CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:4200", "http://127.0.0.1:4200"])

# Service instances (minimal mode - no heavy trading components)
price_service = PriceService()
wallet_service = WalletService()
indicators_service = IndicatorService()

# WebSocket-Preisfeed starten (wie in api_only.py) — ohne diesen Aufruf ist der
# Preis-Cache immer leer und jeder /api/price-Request fällt auf den langsamen
# REST-Fallback (~3s pro Request statt ~0ms aus dem Cache).
PriceService.start()

# Globale Instanzen - minimal
data_manager = None
brain = None
executor = None
trading_active = False
trading_thread = None

# Aktuelle Auswahl
current_symbol = 'BTCUSDT'
current_timeframe = '1h'

# Trades History
TRADES_HISTORY_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'trades', 'trades_history.json'))


def initialize_system():
    """Initialisiere das Trading System (minimal mode)."""
    global data_manager

    logger.info("Initialisiere Trading System (Minimal Mode)...")

    # Data Manager minimal - nur für Price-Service Zugriff
    # Vollständiger Data Manager wird bei Bedarf nachgerüstet
    try:
        from backend.data.data_manager import get_data_manager
        data_manager = get_data_manager()
        data_manager.start()
    except Exception as e:
        logger.warning(f'Full data manager not available in minimal mode: {e}')
        data_manager = None


# ==================== NEW MINIMAL ROUTES ====================

@app.route('/api/price')
def api_price():
    """Get live price for a coin."""
    coin = request.args.get('coin', '').strip()
    if not coin:
        return jsonify({"error": "Missing coin parameter", "data": None}), 400

    result = price_service.get_price_sync(coin)
    if result is None or 'error' in result:
        return jsonify({"error": "Coin not found", "data": None}), 404

    return jsonify(result)


@app.route('/api/wallet')
def api_wallet():
    """Get Binance Spot wallet balances."""
    result = wallet_service.get_wallet_sync()
    if result is None or 'error' in result:
        return jsonify({"error": "Could not fetch wallet", "data": None}), 500
    return jsonify(result)


@app.route('/api/indicators')
def api_indicators_view():
    """Indikator-Daten für ein Coin/Timeframe-Paar.

    Query-Parameter:
        coin: Coin-Bezeichnung ohne /USDT-Suffix (z. B. "btc")
        tf: Timeframe (optional, Standard: "1h")
    """
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
    """API Status"""
    return jsonify({
        'status': 'running' if trading_active else 'stopped',
        'symbol': current_symbol,
        'timeframe': current_timeframe,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    """Einstellungen"""
    global current_symbol, current_timeframe

    if request.method == 'POST':
        data = request.json
        current_symbol = data.get('symbol', current_symbol)
        current_timeframe = data.get('timeframe', current_timeframe)

        return jsonify({'success': True, 'symbol': current_symbol, 'timeframe': current_timeframe})

    return jsonify({
        'symbol': current_symbol,
        'timeframe': current_timeframe
    })


# ==================== TRADES ROUTES ====================

def _load_trades() -> list:
    """Load trades history from JSON file."""
    try:
        with open(TRADES_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {TRADES_HISTORY_FILE}")
        return []


@app.route('/api/trades')
def api_get_trades():
    """Get trades history."""
    trades = _load_trades()
    return jsonify(trades)


@app.route('/api/trades', methods=['POST'])
def api_create_trade():
    """Create a new trade."""
    data = request.json or {}
    trades = _load_trades()

    # Generate new ID
    trade_id = f"TRD{len(trades) + 1:05d}"
    trade = {
        'id': trade_id,
        'symbol': data.get('symbol', ''),
        'timeframe': data.get('timeframe', '1h'),
        'side': data.get('side', 'long'),
        'entry_price': float(data.get('entry_price', 0)),
        'quantity': float(data.get('quantity', 0)),
        'stop_loss': float(data.get('stop_loss', 0)),
        'take_profit': float(data.get('take_profit', 0)),
        'status': 'open',
        'open_time': datetime.now().isoformat(),
        'close_time': None,
        'pnl': 0,
        'pnl_percent': 0,
        'notes': data.get('notes', ''),
        'sl_source': data.get('sl_source', 'sr_level')
    }
    trades.append(trade)
    with open(TRADES_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(trades, f, indent=2, ensure_ascii=False)

    return jsonify({'success': True, 'trade': trade})


@app.route('/api/trades/<trade_id>', methods=['PUT'])
def api_update_trade(trade_id: str):
    """Update a trade (e.g., close it)."""
    trades = _load_trades()
    trade = None
    for t in trades:
        if t.get('id') == trade_id:
            trade = t
            break

    if trade is None:
        return jsonify({'error': 'Trade not found'}), 404

    data = request.json or {}
    for field in ['status', 'close_time', 'pnl', 'pnl_percent', 'notes']:
        if field in data:
            trade[field] = data[field]

    with open(TRADES_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(trades, f, indent=2, ensure_ascii=False)

    return jsonify({'success': True, 'trade': trade})


# ==================== ANGULAR FRONTEND ====================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_angular(path: str):
    """Serve Angular assets and route requests to the Angular SPA."""
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404

    index_file = os.path.join(angular_dist, 'index.html')
    if not os.path.isfile(index_file):
        return jsonify({
            'error': (
                'Angular build not found. Run npm install and npm run build '
                'in frontend/angular.'
            )
        }), 503

    requested_file = safe_join(angular_dist, path) if path else None
    if requested_file and os.path.isfile(requested_file):
        return send_from_directory(angular_dist, path)
    return send_from_directory(angular_dist, 'index.html')


# ==================== MAIN ====================

if __name__ == '__main__':
    # Initialisiere System
    initialize_system()

    # Starte Flask App
    app.run(debug=False, host='127.0.0.1', port=config.DASHBOARD_PORT, use_reloader=False)