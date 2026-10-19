# 06: Vertical Slice — Dashboard & Trade History

**What to build:** The end-to-end path: user opens dashboard → sees real-time prices, bot signals, open trades with P&L, portfolio status, and trade history with performance stats. All data flows through the new REST API endpoints.

**Blocked by:** 03, 04, 05

**Status:** ready-for-agent

- [ ] `templates/dashboard.html` updated: API calls point to FastAPI `/api/v1/` endpoints instead of old Flask routes
- [ ] Dashboard displays: current price, aggregated signal with confidence, per-bot probability breakdown (buy%/sell%/hold%), open trades table (ID, symbol, side, entry, SL, TP), portfolio status (capital, daily P&L, halted indicator)
- [ ] Trade history section shows performance stats: total trades, winning trades, losing trades, win rate, total P&L
- [ ] REST `GET /trades` and `GET /trades/history` endpoints return correct data
- [ ] MCP `get_open_trades` and `get_trade_history` tools return identical data
- [ ] Date range filtering on trade history works
- [ ] CORS enabled so dashboard (port 5000) can call REST API (port 8000)
- [ ] No console errors in browser, all data populates correctly