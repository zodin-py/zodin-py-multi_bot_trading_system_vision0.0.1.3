# Ticket 04: Indicators service + /api/indicators route

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

The old `/api/indicators` endpoint returns single-point indicator values from the bot system. We need a new endpoint that returns the last 20 values for RSI, MACD, and EMA using tradingview-ta.

## Acceptance Criteria

- Create `backend/services/indicators_service.py` with an `IndicatorsService` class
- Use `tradingview-ta` library to fetch indicators (RSI, MACD, EMA)
- Accept `coin` and `tf` query parameters
- Return last 20 indicator values as arrays
- Timeframe is required and must be valid
- Add `GET /api/indicators?coin=btc&tf=1h` to the Flask app
- Add pytest tests

## API Contract

```
GET /api/indicators?coin=btc&tf=1h
→ {
    "rsi": [55.2, 54.8, 53.1, ... 20 values],
    "macd": [120.5, 118.3, 115.9, ... 20 values],
    "ema": [67000.0, 66950.0, 66900.0, ... 20 values],
    "timeframe": "1h",
    "symbol": "BTC/USDT"
  }

GET /api/indicators?coin=invalid&tf=1h
→ {
    "error": "Coin not found",
    "data": null
  }
```

## Implementation Notes

- `tradingview-ta` returns single-point analysis; to get 20 values we need to:
  1. Fetch OHLCV candles via ccxt (last ~50 candles to ensure enough for 20 indicator values)
  2. Compute RSI, MACD, EMA arrays from the candle data using pandas-ta or numpy
- Actually, per spec: "indicators to be read via tradingview-ta". But tradingview-ta only gives current values. The spec says "last 20 indicator values returned".
- Decision: use ccxt to fetch historical candles, then compute indicators locally with pandas-ta (which is already a dependency). This is more accurate for time-series than tradingview-ta.
- Wait — spec says "indicators to be read via tradingview-ta, so that calculation is consistent with TradingView". But tradingview-ta doesn't provide historical series.
- Resolution: use tradingview-ta for the current snapshot (what the spec emphasizes), but for the 20-value history, fetch candles via ccxt and compute with pandas-ta. Document this in the service.
- Actually re-reading spec: "As an user, I want indicators to be read via tradingview-ta". This is the primary requirement. For the 20-value history, we can compute from candles. Let me use a hybrid approach: tradingview-ta for current values, pandas-ta on fetched candles for history.
- Simpler approach: just use pandas-ta on ccxt candles for everything. The spec's mention of tradingview-ta is about consistency, but pandas-ta is standard. Let me check what the existing code does...
- The existing `tradingview_provider.py` already uses `tradingview-ta`. I'll keep using it for the current snapshot, and add local computation for history.
- For the 20-value arrays: fetch ~40 candles from ccxt, compute RSI/MACD/EMA with pandas-ta, return last 20 of each.

## Tests

- `test_indicators_service_returns_arrays`: verifies 20-value arrays for rsi, macd, ema
- `test_indicators_service_invalid_coin`: verifies error response
- `test_indicators_service_default_timeframe`: verifies '1h' default when tf not provided
- `test_api_indicators_endpoint`: integration test via Flask test client
