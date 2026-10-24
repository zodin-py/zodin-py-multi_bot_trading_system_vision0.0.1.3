# 02: DI Container

**What to build:** A `container.py` that creates all shared services exactly once (MarketData, IndicatorProvider, AnalysisService, TradeService, Executor, TradeRepository, PortfolioService, RiskService) and provides them via constructor injection. Replaces all global singleton getters (`get_analysis_service()`, `get_trade_service()`, etc.).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `container.py` created at backend root
- [ ] `Container` class with `build()` method returning fully wired service instances
- [ ] Services instantiated once: MarketData, IndicatorProvider (tradingview-ta + local fallback), IndicatorCalculator (local), AnalysisService, Brain, TradeExecutor, TradeRepository, PortfolioService, RiskService
- [ ] Constructor injection: each service receives dependencies via `__init__`, no global imports
- [ ] `container.py` exposes `get_container()` singleton for app factory
- [ ] All existing singleton getter functions removed/deprecated
- [ ] Type hints for all services
- [ ] Works with both FastAPI (via `dependencies.py`) and MCP server