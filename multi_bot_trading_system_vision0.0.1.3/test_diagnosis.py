#!/usr/bin/env python3
"""Test script to diagnose Binance data loading issues"""

import sys
sys.path.insert(0, '.')

print("[TEST] Starting diagnosis...")

try:
    from config import COINS, BASE_URL
    print(f"[OK] Config loaded. BASE_URL: {BASE_URL}")
    print(f"[OK] Coins available: {len(COINS)}")
except Exception as e:
    print(f"[FAIL] Config error: {e}")
    sys.exit(1)

try:
    from data import get_data_manager
    data_manager = get_data_manager()
    print(f"[OK] DataManager created")
except Exception as e:
    print(f"[FAIL] DataManager error: {e}")
    sys.exit(1)

try:
    print("\n[TEST] Loading historical data for BTCUSDT (1h)...")
    result = data_manager.load_historical_data('BTCUSDT', '1h')
    print(f"[{result}] Historical data load result")
    
    price = data_manager.get_current_price('BTCUSDT')
    print(f"[OK] Current price: {price}")
    
    candles = data_manager.get_candles('BTCUSDT', '1h')
    print(f"[OK] Loaded {len(candles)} candles")
    
    if len(candles) > 0:
        latest = candles[-1]
        print(f"[OK] Latest candle close: {latest['close']}")
    else:
        print(f"[FAIL] No candles loaded!")
        
except Exception as e:
    print(f"[FAIL] Error loading data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[SUCCESS] All tests passed!")
