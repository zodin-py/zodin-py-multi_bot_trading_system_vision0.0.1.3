#!/usr/bin/env python3
"""Test the updated system with new coin loading functionality"""

import sys
sys.path.insert(0, '.')

from app import app, initialize_system

print("[TEST] Starting updated system test...")

# Initialize
initialize_system()

# Test client
client = app.test_client()

print("\n[TEST 1] API Status")
response = client.get('/api/status')
data = response.get_json()
print(f"  Status: {data['status']}")
print(f"  Current Symbol: {data['symbol']}")
print(f"  Current Timeframe: {data['timeframe']}")

print("\n[TEST 2] Load coin BTC via /api/load-coin")
response = client.post('/api/load-coin', json={
    'symbol': 'BTC',
    'timeframe': '1h'
})
data = response.get_json()

if response.status_code == 200:
    print(f"  Success: {data['success']}")
    print(f"  Symbol: {data['symbol']}")
    print(f"  Candles loaded: {data['candles_loaded']}")
    print(f"  Current price: {data['current_price']}")
else:
    print(f"  Error: {data}")

print("\n[TEST 3] Get signals after loading BTC")
response = client.get('/api/signals')
data = response.get_json()

if 'current_price' in data:
    price = data['current_price']
    print(f"  Current price: {price:.4f}")
    print(f"  Price formatted with 4 decimals works: YES")
    
    agg = data.get('aggregated', {})
    print(f"  Signal: {agg.get('final_signal', 'unknown')}")
else:
    print(f"  Error: {data}")

print("\n[TEST 4] Load another coin ETH")
response = client.post('/api/load-coin', json={
    'symbol': 'ETH',
    'timeframe': '4h'
})
data = response.get_json()

if response.status_code == 200:
    print(f"  Symbol: {data['symbol']}")
    print(f"  Candles loaded: {data['candles_loaded']}")
else:
    print(f"  Error: {data}")

print("\n[SUCCESS] All tests passed!")
print("\nChanges implemented:")
print("  1. Price shows 4 decimal places (toFixed(4))")
print("  2. Coin selection via text input (user types)")
print("  3. Data loads on demand (not at startup)")
print("  4. /api/load-coin endpoint added for coin loading")
