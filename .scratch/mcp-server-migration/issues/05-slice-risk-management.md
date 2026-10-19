# 05: Vertical Slice — Risk Management & Portfolio

**What to build:** The end-to-end path: user sets max daily loss limit → system tracks daily P&L → when loss reaches limit, trading halts automatically → user can view portfolio status (capital, daily P&L, open trade count, halted state). Exposed via MCP `set_risk_limit`/`get_portfolio` and REST `POST /risk-limit`/`GET /portfolio`.

**Blocked by:** 04

**Status:** ready-for-agent

- [ ] `MAX_DAILY_LOSS` state machine implemented: `TRADING_ACTIVE --[daily_loss >= MAX_DAILY_LOSS]--> TRADING_HALTED`
- [ ] Loss limit resets daily at 00:00 UTC or via manual reset
- [ ] `TRADE_COOLDOWN_SEC` prevents rapid-fire entries after a loss
- [ ] `mcp/server.py` registers `set_risk_limit` and `get_portfolio` tools
- [ ] `api/server.py` exposes `POST /risk-limit` and `GET /portfolio` endpoints
- [ ] `get_portfolio` returns `{capital, daily_pnl, open_count, is_halted}`
- [ ] `set_risk_limit` accepts `{max_daily_loss_eur}` and returns `{success, current_limit}`
- [ ] Dashboard displays daily P&L, halted state indicator, and risk limit adjustment UI
- [ ] When halted, all new trades are refused with clear error message