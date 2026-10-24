# 04: Data Domain Split

**What to build:** Move market data logic into `domains/data/` with clear separation: REST client, WebSocket stream, cache bridge, service layer, and repository.

**Blocked by:** 03-domain-structure-skeleton

**Status:** ready-for-agent

- [ ] `domains/data/models.py` — Pydantic models for OHLCV, Ticker, OrderBook
- [ ] `domains/data/rest_client.py` — ccxt async REST client (from `data/market_data.py`)
- [ ] `domains/data/ws_stream.py` — Binance WebSocket stream (from `data/market_data.py`)
- [ ] `domains/data/cache.py` — DuckDB cache bridge (from `data/cache.py`)
- [ ] `domains/data/service.py` — `MarketDataService` orchestrating REST + WS + Cache
- [ ] `domains/data/repository.py` — Data access patterns (if needed)
- [ ] `domains/data/__init__.py` exports public API
- [ ] Old `data/market_data.py`, `data/cache.py`, `data/data_manager.py` deprecated (kept for reference, not imported)