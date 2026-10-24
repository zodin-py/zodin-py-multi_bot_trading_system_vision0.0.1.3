# 10: Portfolio & Risk Domain

**What to build:** Separate portfolio aggregation and risk management into dedicated domains.

**Blocked by:** 08-execution-domain-split, 09-trades-domain

**Status:** completed

- [ ] **Portfolio Domain:**
  - [ ] `domains/portfolio/models.py` — `Portfolio`, `CapitalSnapshot`, `DailyPnL`, `OpenPosition`
  - [ ] `domains/portfolio/service.py` — `PortfolioService` computing: current capital, daily P&L, open trade count, total P&L, win rate
  - [ ] `domains/portfolio/__init__.py`
- [ ] **Risk Domain:**
  - [ ] `domains/risk/models.py` — `RiskState`, `RiskLimit`, `HaltReason`
  - [ ] `domains/risk/service.py` — `RiskService` managing: daily loss limit checks, trading halt state, cooldown enforcement, position limits
  - [ ] `domains/risk/__init__.py`
- [ ] `RiskService` integrates with `ExecutionService` (pre-trade checks)
- [ ] Old portfolio/risk logic from `execution/executor.py` removed
- [ ] `config.MAX_DAILY_LOSS` and `config.TRADE_COOLDOWN_SEC` referenced but not duplicated