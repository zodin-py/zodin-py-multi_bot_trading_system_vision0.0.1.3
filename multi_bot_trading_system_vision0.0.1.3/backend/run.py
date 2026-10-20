#!/usr/bin/env python3
"""
START THE TRADING SYSTEM
Run this to start the web app on http://localhost:5000
"""

if __name__ == '__main__':
    import sys
    import os
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    from backend.app import app, initialize_system
    from backend.config import DASHBOARD_PORT

    print("=" * 60)
    print("Multi-Bot Trading System - Starting")
    print("=" * 60)

    print("\n[INIT] Initializing system...")
    initialize_system()

    print("\n[READY] System is ready!")
    print(f"\nWeb interface available at: http://127.0.0.1:{DASHBOARD_PORT}")
    print("\nPress CTRL+C to stop\n")

    # Start Flask app
    app.run(debug=False, host='127.0.0.1', port=DASHBOARD_PORT, use_reloader=False)
