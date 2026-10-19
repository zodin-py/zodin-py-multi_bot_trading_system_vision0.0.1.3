# 03: Vertical Slice — Coin Analysis via MCP + REST

**What to build:** The end-to-end path: user inputs a coin symbol → system fetches market data → computes indicators → RSI/MACD/MFI bots analyze → Brain aggregates → user receives buy/sell/hold signal with confidence. Exposed via both MCP `analyze_coin` and REST `POST /analyze`.

**Blocked by:** 01, 02

**Status:** ready-for-agent

- [ ] RSI, MACD, and MFI bots refactored to read pre-computed indicators from `IndicatorProvider` instead of calling custom `_calculate_*` methods
- [ ] `aggregator/brain.py` works with the new bots: weighted score calculation, threshold logic (65%), final signal determination
- [ ] `mcp/server.py` created: MCP server registers `analyze_coin`, `get_indicators`, `get_market_data` tools
- [ ] `api/server.py` created: FastAPI server exposes `POST /analyze`, `GET /indicators`, `GET /market-data` endpoints
- [ ] Both MCP and REST return identical `AggregatedSignal` shape: `{final_signal, confidence, buy_score, sell_score, hold_score, bot_signals, timestamp}`
- [ ] Stale-data detection rejects signals when last candle age > 2x timeframe interval
- [ ] Dashboard shows aggregated signal and per-bot probability breakdown when user inputs a coin