# 12: MCP Integration Refactor

**What to build:** Update MCP server to use the new DI container and domain services instead of old singletons.

**Blocked by:** 02-di-container, 07-analysis-service, 09-trades-domain

**Status:** ready-for-agent

- [ ] `mcp_integration/server.py` updated to receive services from container
- [ ] All MCP tools delegate to domain services (`AnalysisService`, `TradeService`)
- [ ] No direct imports of old `services/analysis_service.py` or `services/trade_service.py`
- [ ] MCP server starts on port 8001 (configurable)
- [ ] Tools: `analyze_coin`, `get_indicators`, `get_market_data`, `open_trade`, `close_trade`, `get_open_trades`, `get_trade_history`, `get_portfolio`, `set_risk_limit`
- [ ] Error handling consistent with FastAPI routes
- [ ] Old MCP integration code cleaned up