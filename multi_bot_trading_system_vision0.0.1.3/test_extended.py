#!/usr/bin/env python3
"""Extended test - Initialize system and test API calls"""

import sys
sys.path.insert(0, '.')

print("[TEST] Starting extended system test...")

try:
    from config import COINS, SIGNAL_THRESHOLDS, BOT_WEIGHTS
    from data import get_data_manager
    from aggregator import Brain
    from bots import SRBot, SMCBot, HarmonicBot, TrendBot
    from indicators import RSIBot, MACDBot, MFIBot
    
    print("[OK] All imports successful")
    
    # Initialize DataManager
    data_manager = get_data_manager()
    
    # Load historical data
    print("[TEST] Loading data for BTCUSDT (1h)...")
    data_manager.load_historical_data('BTCUSDT', '1h')
    price = data_manager.get_current_price('BTCUSDT')
    candles = data_manager.get_candles('BTCUSDT', '1h')
    print(f"[OK] Current price: {price}, Candles: {len(candles)}")
    
    # Create Bots
    print("[TEST] Creating bots...")
    bots = [
        RSIBot(),
        MACDBot(),
        MFIBot(),
        SRBot(),
        SMCBot(),
        HarmonicBot(),
        TrendBot()
    ]
    print(f"[OK] Created {len(bots)} bots")
    
    # Create Brain
    print("[TEST] Creating Brain...")
    brain = Brain(bots)
    print("[OK] Brain created")
    
    # Test aggregated signal
    print("[TEST] Getting aggregated signal...")
    signal = brain.aggregate_signals('BTCUSDT', '1h', data_manager)
    print(f"[OK] Signal: {signal.final_signal.value}, Confidence: {signal.confidence}%")
    print(f"    Buy: {signal.buy_score:.2f}, Sell: {signal.sell_score:.2f}, Hold: {signal.hold_score:.2f}")
    
    # Test bot probabilities
    print("[TEST] Getting bot probabilities...")
    probs = brain.get_bot_probabilities('BTCUSDT', '1h', data_manager)
    print(f"[OK] Got probabilities for {len(probs)} bots:")
    for bot_name, data in probs.items():
        print(f"    {bot_name}: Buy={data['buy']}%, Sell={data['sell']}%, Hold={data['hold']}%")
    
    print("\n[SUCCESS] All extended tests passed!")
    
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
