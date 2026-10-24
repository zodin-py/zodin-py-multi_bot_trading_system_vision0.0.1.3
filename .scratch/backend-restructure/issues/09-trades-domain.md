# 09: Trades Domain

**What to build:** Move trade lifecycle and history into `domains/trades/` with repository pattern for persistence.

**Blocked by:** 08-execution-domain-split, 07-analysis-service

**Status:** completed

- [ ] `domains/trades/models.py` — `Trade`, `TradeType`, `PnLResult`, `TradeSummary` Pydantic models
- [ ] `domains/trades/repository.py` — Trade persistence (JSON file reading/writing, query helpers)
- [ ] `domains/trades/service.py` — `TradesService` exposing: `open_trade()`, `close_trade()`, `get_open_trades()`, `get_trade_history()`
- [ ] `domains/trades/__init__.py` exports public API
- [ ] Date filtering for trade history queries
- [ ] Trade ID generation (UUID)
- [ ] Old `services/trade_service.py` deprecated
- [ ] JSON persistence at `trades/trades_history.json` (preserved, may migrate to DuckDB later)