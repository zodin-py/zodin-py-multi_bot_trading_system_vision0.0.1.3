# 08: Execution Domain Split

**What to build:** Split the monolithic `execution/executor.py` (648 lines) into focused modules in `domains/execution/`.

**Blocked by:** 03-domain-structure-skeleton, 02-di-container

**Status:** ready-for-agent

- [ ] `domains/execution/models.py` — `Trade`, `Order`, `Position`, `OrderSide`, `OrderType`, `TradeStatus` Pydantic models
- [ ] `domains/execution/order_executor.py` — ccxt order placement (market/limit), Binance Testnet integration
- [ ] `domains/execution/position_sizer.py` — Position sizing logic (risk %, account balance, leverage)
- [ ] `domains/execution/risk_guard.py` — Pre-trade checks: max open trades, daily loss limit, cooldown, symbol exposure
- [ ] `domains/execution/sl_tp_calculator.py` — Dynamic SL/TP from SR levels (2:1 RR) or ATR fallback
- [ ] `domains/execution/service.py` — `ExecutionService` orchestrating the above
- [ ] `domains/execution/repository.py` — Trade persistence (JSON file → later DuckDB)
- [ ] `domains/execution/__init__.py` exports public API
- [ ] Old `execution/executor.py` deprecated
- [ ] All logic testable in isolation