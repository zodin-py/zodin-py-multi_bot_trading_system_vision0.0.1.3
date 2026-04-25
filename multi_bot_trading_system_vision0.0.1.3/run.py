#!/usr/bin/env python3
"""
START THE TRADING SYSTEM
Run this to start the web app on http://localhost:5000
"""

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    
    from app import app, initialize_system
    
    print("=" * 60)
    print("Multi-Bot Trading System - Starting")
    print("=" * 60)
    
    print("\n[INIT] Initializing system...")
    initialize_system()
    
    print("\n[READY] System is ready!")
    print("\nWeb interface available at: http://localhost:5000")
    print("\nPress CTRL+C to stop\n")
    
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
