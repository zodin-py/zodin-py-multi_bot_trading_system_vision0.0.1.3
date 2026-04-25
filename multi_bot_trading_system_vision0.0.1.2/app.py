# filepath: app.py
"""
Multi-Bot Trading System - Flask Web Interface
"""

import logging
import os
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

from aggregator import Brain
from bots import SRBot, SMCBot, HarmonicBot, TrendBot
from config import COINS, TIMEFRAMES, REFRESH_INTERVAL
from data import get_data_manager
from execution import Executor
from indicators import RSIBot, MACDBot, MFIBot


# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)
app.secret_key = 'trading_system_secret_key'

# Globale Instanzen
data_manager = None
brain = None
executor = None
trading_active = False
trading_thread = None

# Aktuelle Auswahl
current_symbol = 'BTCUSDT'
current_timeframe = '1h'


def initialize_system():
    """Initialisiere das Trading System"""
    global data_manager, brain, executor
    
    logger.info("Initialisiere Trading System...")
    
    # Data Manager
    data_manager = get_data_manager()
    
    # Lade historische Daten für alle Coins
    for coin in COINS[:5]:  # Nur die ersten 5 für Performance
        for tf in ['1h', '4h']:
            data_manager.load_historical_data(coin, tf)
    
    # Starte Data Manager WebSocket
    data_manager.start()
    
    # Erstelle Bots
    bots = [
        RSIBot(),
        MACDBot(),
        MFIBot(),
        SRBot(),
        SMCBot(),
        HarmonicBot(),
        TrendBot()
    ]
    
    # Brain
    brain = Brain(bots)
    
    # Executor
    executor = Executor()
    
    logger.info("Trading System initialisiert")


def trading_loop():
    """Hauptschleife für automatisiertes Trading"""
    global trading_active
    
    while trading_active:
        try:
            # Hole aktuellen Preis
            current_price = data_manager.get_current_price(current_symbol)
            
            if current_price > 0:
                # Aggregiere Signale
                signal = brain.aggregate_signals(current_symbol, current_timeframe, data_manager)
                
                # Prüfe Trade-Bedingungen
                if signal.final_signal.value == 'buy' and signal.confidence >= 65:
                    # Öffne Long Trade
                    if len(executor.get_open_trades()) < 5:
                        trade = executor.open_trade(
                            current_symbol,
                            current_timeframe,
                            signal.final_signal,
                            current_price,
                            data_manager
                        )
                        if trade:
                            logger.info(f"Opened trade: {trade.id}")
                
                elif signal.final_signal.value == 'sell' and signal.confidence >= 65:
                    # Öffne Short Trade
                    if len(executor.get_open_trades()) < 5:
                        trade = executor.open_trade(
                            current_symbol,
                            current_timeframe,
                            signal.final_signal,
                            current_price,
                            data_manager
                        )
                        if trade:
                            logger.info(f"Opened trade: {trade.id}")
                
                # Prüfe SL/TP
                trades_to_close = executor.check_trade_conditions(current_symbol, current_price)
                for trade_id in trades_to_close:
                    executor.close_trade(trade_id, reason='TP/SL reached')
            
            # Warte vor dem nächsten Cycle
            time.sleep(REFRESH_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(5)


def start_trading():
    """Starte automatisiertes Trading"""
    global trading_active, trading_thread
    
    if not trading_active:
        trading_active = True
        trading_thread = threading.Thread(target=trading_loop, daemon=True)
        trading_thread.start()
        logger.info("Trading gestartet")


def stop_trading():
    """Stoppe automatisiertes Trading"""
    global trading_active
    
    trading_active = False
    if trading_thread:
        trading_thread.join(timeout=5)
    logger.info("Trading gestoppt")


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Hauptseite - Dashboard"""
    return render_template('dashboard.html',
                           coins=COINS,
                           timeframes=TIMEFRAMES,
                           current_symbol=current_symbol,
                           current_timeframe=current_timeframe)


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
        
        # Lade Daten für das neue Symbol
        data_manager.load_historical_data(current_symbol, current_timeframe)
        
        return jsonify({'success': True, 'symbol': current_symbol, 'timeframe': current_timeframe})
    
    return jsonify({
        'symbol': current_symbol,
        'timeframe': current_timeframe
    })


@app.route('/api/trading', methods=['POST'])
def api_trading():
    """Trading starten/stoppen"""
    global trading_active
    
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        start_trading()
        return jsonify({'status': 'started'})
    elif action == 'stop':
        stop_trading()
        return jsonify({'status': 'stopped'})
    
    return jsonify({'error': 'Invalid action'})


@app.route('/api/signals')
def api_signals():
    """Bot-Signale"""
    if not brain:
        return jsonify({'error': 'System not initialized'})
    
    # Hole Bot-Wahrscheinlichkeiten
    probabilities = brain.get_bot_probabilities(current_symbol, current_timeframe, data_manager)
    
    # Hole aggregiertes Signal
    aggregated = brain.aggregate_signals(current_symbol, current_timeframe, data_manager)
    
    return jsonify({
        'bot_probabilities': probabilities,
        'aggregated': aggregated.to_dict(),
        'current_price': data_manager.get_current_price(current_symbol)
    })


@app.route('/api/indicators')
def api_indicators():
    """Indikator-Daten"""
    if not brain:
        return jsonify({'error': 'System not initialized'})
    
    # Hole RSI
    rsi_bot = next((b for b in brain.bots if b.name == 'RSI'), None)
    rsi_signal = rsi_bot.analyze(current_symbol, current_timeframe, data_manager) if rsi_bot else None
    
    # Hole MACD
    macd_bot = next((b for b in brain.bots if b.name == 'MACD'), None)
    macd_signal = macd_bot.analyze(current_symbol, current_timeframe, data_manager) if macd_bot else None
    
    # Hole MFI
    mfi_bot = next((b for b in brain.bots if b.name == 'MFI'), None)
    mfi_signal = mfi_bot.analyze(current_symbol, current_timeframe, data_manager) if mfi_bot else None
    
    return jsonify({
        'rsi': {
            'value': rsi_signal.details.get('rsi', 0) if rsi_signal else 0,
            'signal': rsi_signal.signal_type.value if rsi_signal else 'hold',
            'confidence': rsi_signal.confidence if rsi_signal else 0
        },
        'macd': {
            'macd_line': macd_signal.details.get('macd_line', 0) if macd_signal else 0,
            'signal_line': macd_signal.details.get('signal_line', 0) if macd_signal else 0,
            'signal': macd_signal.signal_type.value if macd_signal else 'hold',
            'confidence': macd_signal.confidence if macd_signal else 0
        },
        'mfi': {
            'value': mfi_signal.details.get('mfi', 0) if mfi_signal else 0,
            'signal': mfi_signal.signal_type.value if mfi_signal else 'hold',
            'confidence': mfi_signal.confidence if mfi_signal else 0
        }
    })


@app.route('/api/trades')
def api_trades():
    """Offene Trades"""
    if not executor:
        return jsonify({'error': 'Executor not initialized'})
    
    trades = executor.get_open_trades()
    return jsonify({
        'trades': [t.to_dict() for t in trades],
        'count': len(trades)
    })


@app.route('/api/trades/<trade_id>', methods=['DELETE'])
def api_close_trade(trade_id):
    """Trade schließen"""
    if not executor:
        return jsonify({'error': 'Executor not initialized'})
    
    trade = executor.close_trade(trade_id, reason='manual')
    if trade:
        return jsonify({'success': True, 'trade': trade.to_dict()})
    
    return jsonify({'error': 'Trade not found'})


@app.route('/api/history')
def api_history():
    """Trade Historie"""
    if not executor:
        return jsonify({'error': 'Executor not initialized'})
    
    # Filter nach Datum
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    trades = executor.get_trade_history(start, end)
    stats = executor.get_performance_stats(start, end)
    
    return jsonify({
        'trades': [t.to_dict() for t in trades],
        'stats': stats
    })


@app.route('/api/capital')
def api_capital():
    """Kapital"""
    if not executor:
        return jsonify({'error': 'Executor not initialized'})
    
    return jsonify({
        'capital': executor.capital
    })


# ==================== MAIN ====================

if __name__ == '__main__':
    # Initialisiere System
    initialize_system()
    
    # Starte Flask App
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)