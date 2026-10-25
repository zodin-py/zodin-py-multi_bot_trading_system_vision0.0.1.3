# filepath: app.py
"""Multi-Bot Trading System - Flask Web Interface (Minimal Mode)"""

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

# Globale Instanzen - minimal
data_manager = None
brain = None
executor = None
trading_active = False
trading_thread = None

# Aktuelle Auswahl
current_symbol = 'BTCUSDT'
current_timeframe = '1h'


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