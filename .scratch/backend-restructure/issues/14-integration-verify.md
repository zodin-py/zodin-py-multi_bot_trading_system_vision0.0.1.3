# 14: Integration Verification

**What to build:** End-to-end verification that the restructured backend works correctly — FastAPI serves all endpoints, Angular can call them, trades execute properly.

**Blocked by:** 11-api-routes-split, 12-mcp-integration, 13-config-cleanup

**Status:** ready-for-agent

- [ ] Run `python backend/launcher.py` — both FastAPI and Angular Dev Server start
- [ ] Swagger UI at `http://localhost:8000/docs` loads without errors
- [ ] `/health` returns `{"status": "ok"}`
- [ ] `/api/v1/analyze` returns full signal breakdown (7 bots, aggregated)
- [ ] `/api/v1/indicators` returns RSI, MACD, Stoch, ADX values from TradingView
- [ ] `/api/v1/trades` GET returns empty/open trades list
- [ ] `/api/v1/portfolio` returns capital, daily P&L, halt state
- [ ] `/api/v1/symbols` and `/api/v1/timeframes` return supported values
- [ ] MCP tools work via JSON-RPC
- [ ] `ng serve` on port 4200 loads and connects to FastAPI (no CORS errors)
- [ ] Open trade creation flow: analyze → signal → execute (Testnet)
- [ ] Old files (`app.py`, `api/server.py`, `execution/executor.py`, etc.) still present but not imported
- [ ] Git: commit all changes with descriptive message