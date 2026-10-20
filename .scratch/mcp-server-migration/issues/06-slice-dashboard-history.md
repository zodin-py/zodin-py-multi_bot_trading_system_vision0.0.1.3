# 06: Vertical Slice — Dashboard & Trade History

**What to build:** The end-to-end path: user opens dashboard → sees real-time prices, bot signals, open trades with P&L, portfolio status, and trade history with performance stats. All data flows through the new REST API endpoints.

**Blocked by:** 03, 04, 05

**Status:** ready-for-human

- [x] `templates/dashboard.html` updated: API calls point to FastAPI `/api/v1/` endpoints instead of old Flask routes
- [x] Dashboard displays: current price, aggregated signal with confidence, per-bot probability breakdown (buy%/sell%/hold%), open trades table (ID, symbol, side, entry, SL, TP), portfolio status (capital, daily P&L, halted indicator)
- [x] Trade history section shows performance stats: total trades, winning trades, losing trades, win rate, total P&L
- [x] REST `GET /trades` and `GET /trades/history` endpoints return correct data
- [x] MCP `get_open_trades` and `get_trade_history` tools return identical data
- [x] Date range filtering on trade history works
- [x] CORS enabled so dashboard (port 5000) can call REST API (port 8000)
- [x] No console errors in browser, all data populates correctly

**Answer:**
Implemented Ticket 06: Dashboard & Trade History. Updated `templates/dashboard.html` to use FastAPI `/api/v1/` endpoints for all data calls (analyze, indicators, trades, portfolio, history). Added `current_price` to analyze response. Added CORS middleware to both FastAPI and Flask. Flask routes for trading controls (load-coin, settings, trading toggle, status) remain as they control the automated trading loop. All 36 tests pass.