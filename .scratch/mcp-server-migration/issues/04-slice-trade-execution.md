# 04: Vertical Slice — Trade Execution with Dynamic SL/TP

**What to build:** The end-to-end path: aggregated signal >= 65% confidence → Trend/SR/SMC/Harmonic bots contribute → dynamic SL from Support/Resistance levels → TP at exactly 2x SL distance → real order placed on Binance Testnet via ccxt → open trade tracked. Exposed via MCP `open_trade`/`close_trade` and REST `POST /trades`/`DELETE /trades/{id}`.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Trend, SR, SMC, and Harmonic bots refactored to use `IndicatorProvider` for OHLCV and computed indicators
- [ ] `execution/executor.py` extended: dynamic SL/TP calculation from SR-Bot Support/Resistance levels with 2:1 Risk-Reward ratio
- [ ] Fallback SL/TP works when no S/R level within 2% (ATR-based or percentage-based)
- [ ] `ccxt.create_order()` integrated for real order placement on Binance Testnet
- [ ] Position sizing formula correct: `quantity = (capital * RISK_PERCENT / 100) / |entry_price - SL|`
- [ ] Maximum 5 concurrent open positions enforced
- [ ] `TRADE_COOLDOWN_SEC` cooldown between trades per symbol enforced
- [ ] `mcp/server.py` registers `open_trade`, `close_trade`, `get_open_trades` tools
- [ ] `api/server.py` exposes `POST /trades`, `DELETE /trades/{id}`, `GET /trades` endpoints
- [ ] Trade P&L calculated with actual current price from MarketData (not placeholder entry_price)
- [ ] Dashboard shows open trades with entry price, SL, TP, and side