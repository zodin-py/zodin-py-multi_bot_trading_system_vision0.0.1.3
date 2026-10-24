# 02: DI Container

**What to build:** A `container.py` that creates all shared services exactly once and provides them via constructor injection. Replaces all global singleton getters.

**Blocked by:** None (can start immediately)

**Status:** completed

- [x] `container.py` created at backend root
- [x] `Container` class with `build()` method returning fully wired service instances
- [x] Services instantiated once: MarketData, IndicatorProvider, AnalysisService, TradeService, Executor, TradeRepository, PortfolioService, RiskService
- [x] Constructor injection: each service receives dependencies via `__init__`
- [x] `get_container()` singleton for app factory
- [x] All existing singleton getter functions deprecated
- [x] Type hints for all services
