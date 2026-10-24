# 08: Execution Domain Split

**What to build:** Split monolithic `execution/executor.py` (648 lines) into focused modules.

**Blocked by:** 03-domain-structure-skeleton, 02-di-container

**Status:** completed

- [x] `domains/execution/models.py` — Trade, Order, Position models
- [x] `domains/execution/order_executor.py` — ccxt order placement
- [x] `domains/execution/position_sizer.py` — Position sizing logic
- [x] `domains/execution/risk_guard.py` — Pre-trade checks
- [x] `domains/execution/sl_tp_calculator.py` — Dynamic SL/TP
- [x] `domains/execution/service.py` — `ExecutionService` orchestrating all
- [x] `domains/execution/repository.py` — Trade JSON persistence
- [x] All logic testable in isolation
