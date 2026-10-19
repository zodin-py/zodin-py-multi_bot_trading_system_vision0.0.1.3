# 03: Vertical Slice — Coin Analysis via MCP + REST

**What to build:** The end-to-end path: user inputs a coin symbol → system fetches market data → computes indicators → RSI/MACD/MFI bots analyze → Brain aggregates → user receives buy/sell/hold signal with confidence. Exposed via both MCP `analyze_coin` and REST `POST /analyze`.

**Blocked by:** 01, 02

**Status:** completed

- [x] RSI, MACD, and MFI bots refactored to read pre-computed indicators from `IndicatorProvider` instead of calling custom `_calculate_*` methods
- [x] SR, SMC, Harmonic, Trend bots refactored to use `IndicatorProvider` for OHLCV and indicators
- [x] `aggregator/brain.py` works with the new bots: weighted score calculation, threshold logic (65%), final signal determination
- [x] `mcp_integration/server.py` created: MCP server registers `analyze_coin`, `get_indicators`, `get_market_data`, `get_supported_symbols`, `get_supported_timeframes` tools (plus placeholders for future tickets)
- [x] `api/server.py` created: FastAPI server exposes `POST /analyze`, `GET /analyze`, `POST /indicators`, `GET /indicators`, `POST /market-data`, `GET /market-data` endpoints
- [x] Both MCP and REST return identical `AggregatedSignal` shape: `{final_signal, confidence, buy_score, sell_score, hold_score, bot_signals, timestamp}`
- [x] Stale-data detection rejects signals when last candle age > 2x timeframe interval (implemented in MarketData + Provider)
- [x] Shared `services/analysis_service.py` encapsulates all business logic for both interfaces
- [x] All 7 bots (RSI, MACD, MFI, SR, SMC, Harmonic, Trend) integrated and working

## Comments

- **2026-10-19**: All 7 acceptance criteria met. Full end-to-end test passes: BTC/1h → HOLD signal with 50% confidence, per-bot breakdown available.
- WebSocket connection to Binance Testnet has DNS issues locally (`getaddrinfo failed`), but REST + DuckDB cache works perfectly.
- Module renamed from `mcp/` to `mcp_integration/` to avoid shadowing the installed `mcp` package.