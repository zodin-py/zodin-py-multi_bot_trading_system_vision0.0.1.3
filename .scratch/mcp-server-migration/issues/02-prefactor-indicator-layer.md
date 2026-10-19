# 02: Prefactoring — Indicator Layer

**What to build:** The indicator computation engine and the `IndicatorProvider` protocol that all bots will depend on. This makes bots testable without network access.

**Blocked by:** 01

**Status:** completed

- [x] `indicators/calculator.py` created: uses `ta-lib` (primary) or `pandas-ta` (fallback) for vectorized batch computation of RSI, MACD, MFI, ADX, ATR, SMA, EMA
- [x] Calculator caches results keyed by `(symbol, timeframe, params_hash)` and supports incremental update on new candle close
- [x] Calculator output matches TradingView reference values for known inputs (golden master test)
- [x] `indicators/provider.py` created: `IndicatorProvider` Protocol with `get_indicators(symbol, timeframe) -> Dict` and `get_ohlcv(symbol, timeframe, periods) -> Tuple`
- [x] `MockIndicatorProvider` class created for unit testing bots without network access
- [x] `bots/base_bot.py` refactored: all `_calculate_*` methods removed, `IndicatorProvider` injected via constructor, bots delegate to provider instead of computing locally

## Comments

- **2026-10-19**: All 6 acceptance criteria met. 8/8 golden master tests pass (`tests/test_calculator.py`).
- pandas_ta 0.4.71b0 uses direct function calls (`pandas_ta.rsi(...)`) — NOT `df.ta.rsi()`. Calculator uses direct function calls with pandas Series inputs.
- ta-lib is not installed on this Windows machine; pandas_ta is the primary engine. Calculator has a `use_talib` flag for future upgrade when ta-lib C library is available.
- Adapter (`IndicatorProviderAdapter`) bridges MarketData + Calculator. Mock adapter (`MockIndicatorProviderAdapter`) exists for unit tests without network.