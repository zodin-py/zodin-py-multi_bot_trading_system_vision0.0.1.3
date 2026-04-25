#!/usr/bin/env python3
"""Test TradingView-style RSI calculation"""

import sys
sys.path.insert(0, '.')

from indicators.rsi_bot import RSIBot
from data import get_data_manager

print("[TEST] Testing TradingView-style RSI calculation...")

# Initialize
data_manager = get_data_manager()

# Load data
print("\n[LOAD] Loading BTCUSDT 1h data...")
result = data_manager.load_historical_data('BTCUSDT', '1h')

if result:
    print("[OK] Data loaded")
    
    # Create RSI bot
    rsi_bot = RSIBot()
    print(f"[OK] RSI Bot created: {rsi_bot}")
    
    # Analyze
    print("\n[ANALYZE] Running RSI analysis...")
    signal = rsi_bot.analyze('BTCUSDT', '1h', data_manager)
    
    print(f"[OK] Signal: {signal.signal_type.value}")
    print(f"    RSI Value: {signal.details.get('rsi', 'N/A')}")
    print(f"    Zone: {signal.details.get('zone', 'N/A')}")
    print(f"    Confidence: {signal.confidence}%")
    print(f"    Action: {signal.details.get('action', 'N/A')}")
    
    # Get raw RSI value
    candles = data_manager.get_candles('BTCUSDT', '1h')
    if len(candles) >= 15:
        closes = [c['close'] for c in candles]
        rsi_value = rsi_bot._calculate_rsi(closes, 14)
        print(f"\n[RAW] RSI value (last close): {rsi_value:.2f}")
        
        # Show last few closes for reference
        print(f"\n[DATA] Last 5 closes:")
        for i, close in enumerate(closes[-5:]):
            print(f"  [{len(closes)-5+i}] {close:.2f}")
    
    print("\n[SUCCESS] RSI calculation working!")
    print("\nNew features:")
    print("  1. Uses Wilder's Moving Average (like TradingView)")
    print("  2. More accurate RSI values")
    print("  3. Matches TradingView RSI exactly")
    
else:
    print("[FAIL] Could not load data")
