# 07: Backtest & Tests

**What to build:** A backtesting engine that uses the same indicator engine and bot logic as live trading on historical DuckDB data, plus comprehensive unit tests for all modules and integration testing on Binance Testnet.

**Blocked by:** 03, 04

**Status:** ready-for-agent

- [ ] Backtest engine created: loads historical OHLCV from DuckDB, runs same `IndicatorCalculator`, feeds same bots, aggregates with same `Brain`, simulates trades with same `Executor` logic
- [ ] Backtest tracks performance metrics: total trades, win rate, total P&L, Sharpe ratio, max drawdown
- [ ] Backtest results are deterministic: same seed + same data = same output
- [ ] Unit tests written for all new modules: `calculator.py`, `cache.py`, `market_data.py`, `provider.py`, `mcp/server.py`, `api/server.py`
- [ ] Unit tests written for all refactored bots: `rsi_bot.py`, `macd_bot.py`, `mfi_bot.py`, `trend_bot.py`, `sr_bot.py`, `smc_bot.py`, `harmonic_bot.py`
- [ ] Unit tests for `brain.py` (weighted aggregation, threshold logic) and `executor.py` (SL/TP formulas, position sizing, loss-limit state machine, cooldown)
- [ ] Golden master tests validate indicator outputs against TradingView reference values
- [ ] `pytest` runs successfully with coverage report
- [ ] Integration test on Binance Testnet: coin loading, real-time streaming, indicator calculation, signal aggregation, trade execution, SL/TP monitoring, loss limit, portfolio tracking, MCP tools, REST endpoints