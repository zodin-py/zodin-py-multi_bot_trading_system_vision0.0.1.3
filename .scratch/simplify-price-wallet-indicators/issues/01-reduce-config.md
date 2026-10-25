# Ticket 01: Reduce config to minimum

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

`backend/config.py` contains many fields no longer needed. Strip to minimum required for price, wallet, indicators.

## Acceptance Criteria

- Config keeps only: `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`, `DEFAULT_QUOTE=USDT`, `TIMEFRAMES`, `INDICATOR_PARAMS` (rsi/macd/ema defaults), `API_PORT`, `DASHBOARD_PORT`
- Remove: bot weights, risk management, signal thresholds, backtesting, trades history, refresh interval, cache/DuckDB settings
- Keep Pydantic BaseSettings with env_prefix `TRADING_`
- Keep lazy getter pattern for `get_base_url()` / `get_ws_url()`
- Backward-compatible module-level stub exports for removed fields

## Implementation

Modify `backend/config.py` to strip all non-essential fields while keeping:
- The `TradingConfig` class with only the minimal fields
- Module-level backward-compatible exports
- Lazy getter functions (get_base_url, get_ws_url)
- Pydantic SettingsConfigDict with env_prefix, env_file