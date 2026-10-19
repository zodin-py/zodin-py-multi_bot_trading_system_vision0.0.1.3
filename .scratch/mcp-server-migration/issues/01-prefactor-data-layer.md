# 01: Prefactoring — Data Layer Foundation

**What to build:** The data layer that everything else depends on: updated `requirements.txt`, extended `config.py`, DuckDB-backed persistent cache, and ccxt-based market data access with WebSocket streaming and auto-reconnect.

**Blocked by:** None (can start immediately)

**Status:** completed

- [x] `requirements.txt` updated: removed `binance-connector`, `python-binance`, `websocket-client`, `asyncio`; added `ccxt>=4.4.0`, `duckdb>=1.0.0`, `fastapi>=0.110.0`, `uvicorn>=0.27.0`, `mcp>=1.0.0`, `pandas-ta>=0.3.14b0` (ta-lib as optional fallback)
- [x] `pip install -r requirements.txt` succeeds (verified: ccxt 4.5.88, duckdb 1.5.6, fastapi 0.148.0, mcp, pandas-ta OK)
- [x] `config.py` extended with `MAX_DAILY_LOSS`, `TRADE_COOLDOWN_SEC`, `DYNAMIC_SL_TP_ENABLED`, `CACHE_TTL_SEC`, `DUCKDB_PATH`, `MCP_PORT`, `API_PORT`, `CCXT_RATE_LIMIT`, `USE_TESTNET`
- [x] `data/cache.py` created: DuckDB-backed persistent cache for candles and indicators, keyed by `(symbol, timeframe, timestamp)`, TTL-based cleanup, UPSERT via `executemany`, survives restarts
- [x] `data/market_data.py` created: ccxt REST (`fetch_ohlcv_async`) with rate limiting + native Binance Kline WebSocket (`watch_ohlcv` via combined stream) with auto-reconnect, exponential backoff, stale-data TTL checks (`is_stale`, `should_reject_signal`)

## Comments

- **2026-10-19**: All 5 acceptance criteria met. Live test against Binance Testnet: `fetch_ohlcv_async('BTCUSDT', '1h', limit=5)` returns real candles (close ~81919.95 USDT), `is_stale` returns False, `get_current_price` works.
- DuckDB cache roundtrip verified: store 50 candles, UPSERT works, indicator cache with TTL works, persistence across process restart confirmed.
- ccxt free edition does NOT provide `watch_ohlcv` for Binance Spot → implemented native Binance Kline WebSocket (combined streams) with auto-reconnect and backoff in parallel to ccxt REST. This is the correct architecture: ccxt for REST with built-in rate limiting, native WS for streaming.