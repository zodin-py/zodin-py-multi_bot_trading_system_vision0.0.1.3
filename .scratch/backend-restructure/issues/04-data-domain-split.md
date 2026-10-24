# 04: Data Domain Split

**What to build:** Move market data logic into `domains/data/` with clear separation: REST client, WebSocket stream, cache bridge, service layer, and repository.

**Blocked by:** 03-domain-structure-skeleton

**Status:** completed

- [x] `domains/data/models.py` — Pydantic models for OHLCV, Ticker
- [x] `domains/data/rest_client.py` — ccxt async REST client
- [x] `domains/data/ws_stream.py` — Binance WebSocket stream
- [x] `domains/data/cache.py` — DuckDB cache bridge
- [x] `domains/data/service.py` — `MarketDataService`
- [x] `domains/data/repository.py` — Data access patterns
- [x] `domains/data/__init__.py` exports public API
