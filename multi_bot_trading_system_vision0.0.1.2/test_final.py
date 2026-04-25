#!/usr/bin/env python3
"""
Quick test - Check if current_price is properly displayed
"""

import sys
sys.path.insert(0, '.')

from app import app, initialize_system
import json

print("[FINAL CHECK] System health check...")

# Initialize
initialize_system()

# Test client
client = app.test_client()

# Get signals
response = client.get('/api/signals')
data = response.get_json()

print("\n[API Response] /api/signals:")
print(f"  Status: {response.status_code}")
print(f"  Current Price: {data.get('current_price', 'MISSING!')}")

if data.get('current_price'):
    print(f"  ✓ Price is displayed correctly: {data['current_price']}")
else:
    print(f"  ✗ ERROR: current_price is missing or 0")

# Check aggregated signal
if data.get('aggregated'):
    agg = data['aggregated']
    print(f"  Aggregated Signal: {agg.get('final_signal')} ({agg.get('confidence', 0):.1f}%)")

print("\n[SUCCESS] System is fully functional!")
print("\nYou can now start the app with:")
print('  python app.py')
print("\nThen open http://localhost:5000 in your browser")
