#!/usr/bin/env python3
"""Test Flask app and all API endpoints"""

import sys
sys.path.insert(0, '.')

from app import app, initialize_system, data_manager, brain, executor
import json

print("[TEST] Starting Flask API test...")

# Initialize system
try:
    initialize_system()
    print("[OK] System initialized")
except Exception as e:
    print(f"[FAIL] Initialization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Create test client
client = app.test_client()

# Test endpoints
endpoints = [
    ('GET', '/api/status'),
    ('GET', '/api/settings'),
    ('GET', '/api/signals'),
    ('GET', '/api/indicators'),
    ('GET', '/api/trades'),
    ('GET', '/api/capital'),
]

print("\n[TEST] Testing API endpoints...")
for method, endpoint in endpoints:
    try:
        if method == 'GET':
            response = client.get(endpoint)
        else:
            response = client.post(endpoint)
        
        status = response.status_code
        if status == 200:
            try:
                data = response.get_json()
                print(f"[OK] {method} {endpoint} - Status {status}")
                if isinstance(data, dict):
                    # Print first key
                    if data:
                        first_key = list(data.keys())[0]
                        val = data[first_key]
                        if isinstance(val, (int, float, str, bool)):
                            print(f"       -> {first_key}: {val}")
            except:
                print(f"[WARN] {method} {endpoint} - Status {status} but invalid JSON")
        else:
            print(f"[FAIL] {method} {endpoint} - Status {status}")
            print(f"       Response: {response.get_data(as_text=True)[:200]}")
    except Exception as e:
        print(f"[FAIL] {method} {endpoint} - Error: {e}")

print("\n[SUCCESS] API test completed!")
