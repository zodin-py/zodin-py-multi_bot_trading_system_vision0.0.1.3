# SPEC: Multi-Bot Crypto Trading System mit MCP Server & REST API

Status: ready-for-agent
Date: 2026-10-19
Feature: mcp-server-migration

## Problem Statement

Das bestehende Flask-basierte Multi-Bot-Trading-System (7 Bots: RSI, MACD, MFI, SR, SMC, Harmonic, Trend) verwendet einen `DataManager` der OHLCV-Kerzen via roher `requests.get`-Aufrufe und einer fragilen WebSocket-Verbindung von Binance bezieht. Alle technischen Indikatoren werden lokal in `base_bot.py` mit handgeschriebenen Python-Schleifen berechnet (RMA, EMA, SMA, RSI, MACD, MFI, ADX). Diese Implementierungen sind nicht vektorisiert, nicht battle-tested und werden bei jedem Signalaufruf neu berechnet.

Die in `requirements.txt` deklarierten Bibliotheken (`binance-connector`, `python-binance`, `ta-lib`, `pandas-ta`) werden nirgends importiert oder genutzt. Der `Executor` führt keine echten Orders an der Börse aus — er simuliert Trades nur lokal mit Platzhalter-Preisen. Es gibt kein persistierendes Caching (Daten gehen bei Neustart verloren), kein Rate-Limiting, keine Reconnection-Resilience und kein konfigurierbares Verlustlimit.

Der Benutzer möchte:
- Indikatorwerte abrufen, die bereits berechnet sind (Binance liefert jedoch nur Rohdaten — Indikatoren müssen clientseitig berechnet werden)
- Einen MCP-Server für Claude Code Integration UND eine unabhängige REST-API
- Automatische Trade-Ausführung mit dynamischem SL/TP (2:1 Risk-Reward)
- Konfigurierbares tägliches Verlustlimit
- Paper-Trading auf Binance Testnet, später Live-Trading
- Nur Binance als Exchange, Single-Coin-Analyse (kein Multi-Coin gleichzeitig)

## Solution

Ein **Dual-Interface-System** (MCP + REST) das auf drei neuen Schichten aufbaut:

1. **Data Layer**: `ccxt.async_support` ersetzt rohe `requests`/`websockets`-Aufrufe. Einheitliche `fetch_ohlcv()` (REST) und `watch_ohlcv()` (WebSocket) Methoden mit eingebautem Rate-Limiting und Auto-Reconnect. Persistenter Cache via DuckDB.
2. **Indicator Layer**: `ta-lib` (oder `pandas-ta` als Fallback) ersetzt alle handgeschriebenen Indikator-Berechnungen in `base_bot.py`. Vektorisierte Batch-Berechnung auf DataFrames mit inkrementellem Update bei neuen Kerzen.
3. **Interface Layer**: Ein MCP-Server (Python, stdio) für Claude Code und eine FastAPI REST-API für das Dashboard und unabhängigen Zugriff. Beide teilen denselben Backend-Code.

Die bestehende Bot-Architektur (`Brain`, `Executor`, 7 Bots) bleibt erhalten, wird aber über ein `IndicatorProvider`-Protocol von der Datenquelle entkoppelt.

## User Stories

1. As a Trader, I want to input a single coin symbol (e.g. "BTC") and immediately receive a multi-bot analysis with aggregated buy/sell/hold signal, so that I can make informed trading decisions.
2. As a Trader, I want the system to run on Binance Testnet by default, so that I can validate strategies without risking real money.
3. As a Trader, I want automatic trade execution when the aggregated signal confidence is >= 65%, so that trades open at the right moment without manual confirmation.
4. As a Trader, I want dynamic Stop-Loss calculated from Support/Resistance levels (SR-Bot) with Take-Profit at exactly 2x the SL distance (2:1 Risk-Reward), so that my trades are market-structure-aware.
5. As a Trader, I want to set a maximum daily loss limit (e.g. 10 EUR) that automatically halts all new trades when reached, so that my downside is capped.
6. As a Developer, I want to call analysis and trading functions via MCP tools from Claude Code, so that I can integrate the system into AI-assisted workflows.
7. As a Developer, I want the same functions available via a standalone REST API (FastAPI), so that I am not dependent on Claude Code for programmatic access.
8. As a Trader, I want a web dashboard showing real-time prices, bot signals, open trades with P&L, and trade history, so that I have visual oversight.
9. As a Trader, I want to switch between timeframes (1m, 5m, 15m, 1h, 4h, 1d) for any coin, so that I can analyze multiple horizons.
10. As a Trader, I want the system to survive restarts without losing cached market data or open trade state, so that I don't need to wait for full data warmup after every restart.
11. As a Developer, I want indicator calculations to use battle-tested libraries (ta-lib) instead of custom Python loops, so that values match TradingView and other platforms.
12. As a Trader, I want position sizing based on risk percentage (1% of capital per trade) divided by SL distance, so that my risk per trade is consistent regardless of volatility.
13. As a Trader, I want a maximum of 5 concurrent open positions enforced, so that overexposure is prevented.
14. As a Trader, I want a cooldown period between trades, so that rapid-fire entries after a loss are prevented.
15. As a Developer, I want structured logging with trade events, signal events, and error events, so that debugging production issues is straightforward.
16. As a Trader, I want the bot weights (Trend 0.20, RSI/MACD/SR/SMC 0.15, MFI/Harmonic 0.10) to remain as defaults but be configurable, so that I can tune strategy emphasis.
17. As a Developer, I want the bots decoupled from the DataManager via dependency injection (IndicatorProvider protocol), so that I can swap data sources without modifying bot logic.
18. As a Trader, I want stale-data detection that rejects signals when the last candle is older than 2x the timeframe interval, so that I don't trade on outdated data.
19. As a Developer, I want backtesting support using the same indicator engine on historical DuckDB data, so that strategy validation uses identical code paths as live trading.
20. As a Trader, I want to see each individual bot's probability breakdown (buy%, sell%, hold%) in the dashboard, so that I understand why a signal was generated.

## Implementation Decisions

### Modules to Build

- **data/market_data.py** (new): Replaces `data/data_manager.py`. Wraps `ccxt.async_support` for Binance. Provides `fetch_ohlcv(symbol, timeframe, limit)` for historical data and `watch_ohlcv(symbol, timeframe)` for real-time WebSocket streaming. Includes auto-reconnect with exponential backoff, built-in rate limiting via `enableRateLimit: true`, and stale-data TTL checks.
- **data/cache.py** (new): DuckDB-backed persistent cache for OHLCV candles and computed indicators. Keyed by `(symbol, timeframe, timestamp)`. Survives process restarts. Configurable TTL per timeframe.
- **indicators/calculator.py** (new): Uses `ta-lib` (primary) or `pandas-ta` (fallback) for vectorized indicator computation. Computes RSI, MACD, MFI, ADX, ATR, SMA, EMA in batch on DataFrames. Caches results keyed by `(symbol, timeframe, params_hash)`. Supports incremental update when a new candle closes.
- **indicators/provider.py** (new): Defines the `IndicatorProvider` Protocol class that bots depend on instead of `DataManager`. Interface: `get_indicators(symbol, timeframe) -> Dict[str, Any]` and `get_ohlcv(symbol, timeframe, periods) -> Tuple`.
- **mcp/server.py** (new): MCP server using Python MCP SDK. Runs as stdio process. Exposes tools: `analyze_coin`, `get_indicators`, `get_market_data`, `open_trade`, `close_trade`, `get_open_trades`, `get_trade_history`, `set_risk_limit`, `get_portfolio`.
- **api/server.py** (new): FastAPI REST server exposing the same endpoints as MCP tools. Runs on port 8000. No authentication initially (local-only deployment).

### Modules to Modify

- **bots/base_bot.py**: Remove all `_calculate_*` methods (RSI, MACD, MFI, ADX, EMA, SMA, RMA). Replace with `IndicatorProvider` dependency injection via constructor. Bots call `self.indicator_provider.get_indicators(symbol, tf)` instead of computing locally.
- **indicators/rsi_bot.py**, **macd_bot.py**, **mfi_bot.py**: Refactor `analyze()` to read pre-computed indicator values from `IndicatorProvider` instead of calling `self._calculate_rsi()` etc.
- **bots/trend_bot.py**, **sr_bot.py**, **smc_bot.py**, **harmonic_bot.py**: Same refactoring — use `IndicatorProvider` for OHLCV data and computed indicators.
- **execution/executor.py**: Add dynamic SL/TP calculation using SR-Bot levels. Add `MAX_DAILY_LOSS` enforcement. Add `TRADE_COOLDOWN_SEC` between trades. Replace placeholder price with actual current price from `MarketData`. Integrate `ccxt.create_order()` for Testnet order placement.
- **config.py**: Add new keys: `MAX_DAILY_LOSS` (default 10.0), `TRADE_COOLDOWN_SEC` (default 60), `DYNAMIC_SL_TP_ENABLED` (default True), `CACHE_TTL_SEC`, `DUCKDB_PATH`, `MCP_PORT`, `API_PORT`.
- **requirements.txt**: Remove unused `binance-connector==1.0.1`, `python-binance==1.0.19`, `websocket-client==1.7.0`, `asyncio==3.4.3`. Add `ccxt>=4.4.0`, `duckdb>=1.0.0`, `fastapi>=0.110.0`, `uvicorn>=0.27.0`, `mcp>=1.0.0`. Update `pandas-ta>=0.4.0` (or keep `ta-lib` if buildable).
- **app.py**: Initialize new `MarketData` and `IndicatorCalculator` instead of old `DataManager`. Start both MCP server (subprocess) and FastAPI (thread) alongside Flask dashboard.
- **run.py**: Update startup sequence to initialize new data layer.
- **templates/dashboard.html**: Point API calls to FastAPI endpoints where applicable. Keep Flask routes as proxy or migrate fully to FastAPI.

### Architectural Decisions

- **Dual Interface, Shared Core**: MCP and REST-API are thin wrappers around the same service layer. Business logic lives in `aggregator/brain.py`, `execution/executor.py`, and `indicators/calculator.py` — never in the interface layer.
- **Dependency Inversion for Bots**: Bots depend on `IndicatorProvider` protocol, not on concrete `DataManager` or `MarketData`. This allows unit testing with mock providers and swapping data sources.
- **Persistent Cache over In-Memory**: DuckDB replaces `deque(maxlen=500)`. Provides SQL-queryable historical data, survives restarts, enables backtesting on the same dataset.
- **Single Coin Focus**: The system analyzes one coin at a time as specified by the user. No parallel multi-coin scanning in v1.
- **Local Deployment Only**: Everything runs on the user's Windows machine. No Docker, no cloud deployment in v1.
- **Testnet First**: All exchange interactions default to Binance Testnet (`USE_TESTNET = True`). Switching to live requires explicit config change.

### SL/TP Calculation Schema

```
Long Trade:
  SL = nearest_support_level (from SR-Bot)
  If no support within 2%: SL = entry_price * (1 - ATR_multiplier)
  TP = entry_price + (entry_price - SL) * 2

Short Trade:
  SL = nearest_resistance_level (from SR-Bot)
  If no resistance within 2%: SL = entry_price * (1 + ATR_multiplier)
  TP = entry_price - (SL - entry_price) * 2

Position Size = (capital * RISK_PERCENT / 100) / |entry_price - SL|
```

### Loss Limit State Machine

```
TRADING_ACTIVE --[daily_loss >= MAX_DAILY_LOSS]--> TRADING_HALTED
TRADING_HALTED --[manual reset OR daily reset at 00:00 UTC]--> TRADING_ACTIVE
```

### MCP Tool Contracts

| Tool | Input | Output |
|------|-------|--------|
| `analyze_coin` | `{symbol, timeframe}` | `AggregatedSignal` dict |
| `get_indicators` | `{symbol, timeframe}` | `{rsi, macd, macd_signal, macd_hist, mfi, adx, plus_di, minus_di, atr}` |
| `get_market_data` | `{symbol, timeframe, limit}` | OHLCV array |
| `open_trade` | `{symbol, side, entry_price, sl, tp}` | `Trade` dict |
| `close_trade` | `{trade_id, reason}` | `Trade` dict |
| `get_open_trades` | `{}` | Array of `Trade` dicts |
| `get_trade_history` | `{start_date?, end_date?}` | Array of `Trade` dicts + stats |
| `set_risk_limit` | `{max_daily_loss_eur}` | `{success, current_limit}` |
| `get_portfolio` | `{}` | `{capital, daily_pnl, open_count, is_halted}` |

### REST API Endpoints (mirrors MCP)

All under `/api/v1/`. Same request/response shapes as MCP tools. Standard HTTP methods (GET for reads, POST for actions, DELETE for close trade).

## Testing Decisions

### What Makes a Good Test

Tests verify external behavior (signal output, trade creation, SL/TP values, loss-limit enforcement) not internal implementation details (which moving average formula is used inside ta-lib). Tests use fixture data — known OHLCV arrays with expected indicator outputs validated against TradingView reference values.

### Seams for Testing

The primary testing seam is the **`IndicatorProvider` protocol**. By injecting a mock provider into bots, every bot can be tested deterministically without network access or real exchange data. This is the single highest-value seam in the codebase.

Secondary seams:
- **`MarketData.fetch_ohlcv`**: Mock ccxt responses for data layer tests.
- **`Executor.open_trade` / `close_trade`**: Test SL/TP math and loss-limit state transitions with controlled inputs.
- **`Brain.aggregate_signals`**: Test weighted aggregation with fixture bot signals.

### Modules to Test

| Module | Test Type | What to Verify |
|--------|-----------|----------------|
| `indicators/calculator.py` | Golden Master | ta-lib/pandas-ta output matches TradingView reference values for RSI(14), MACD(12,26,9), MFI(14), ADX(14) |
| `bots/rsi_bot.py` | Unit | Given fixture indicators → correct signal type and confidence |
| `bots/macd_bot.py` | Unit | Crossover detection logic with fixture MACD values |
| `bots/sr_bot.py` | Unit | Support/resistance level detection from fixture OHLCV |
| `aggregator/brain.py` | Unit | Weighted score calculation, threshold logic (65%), final signal determination |
| `execution/executor.py` | Unit | SL/TP formulas (2:1 ratio), position sizing, loss-limit halt trigger, cooldown enforcement |
| `data/cache.py` | Integration | DuckDB write/read roundtrip, TTL expiry, persistence across simulated restart |
| `mcp/server.py` | Contract | JSON schema of tool inputs/outputs matches spec |
| `api/server.py` | Contract | HTTP status codes, response shapes match MCP equivalents |

### Prior Art

The existing `test_rsi_tradingview.py`, `test_api.py`, `test_final.py` files in the project test the old custom implementations. These serve as reference for expected behavior but will need updating once ta-lib replaces the custom math. The test patterns (direct function calls with fixture data) should be preserved.

## Out of Scope

- Multi-exchange support (only Binance Spot)
- Futures, perpetuals, leverage trading (Spot only)
- WebSocket push to dashboard (polling every 5s for v1)
- Telegram, Discord, or email notifications (dashboard only)
- Authentication or RBAC on the REST API (local-only deployment)
- Cloud deployment, Docker containerization, Kubernetes
- ML/AI-based signal enhancement (rule-based only)
- Portfolio optimization or multi-asset allocation (single-coin focus)
- Multi-coin simultaneous scanning (user selects one coin at a time)
- CCXT Pro paid tier (use free `ccxt.async_support` WebSocket)

## Further Notes

- **Critical finding from research**: Binance Spot API does NOT provide pre-calculated indicator values. All indicators must be computed client-side from raw OHLCV klines. The user's assumption that "Binance already calculates RSI/MACD/MFI" applies to the Binance UI/app display, not the API. The `ta-lib` library is essential.
- **Existing code preservation**: The bot logic (Brain aggregation, signal types, confidence scoring), Executor trade management, Flask dashboard UI, and configuration structure are all retained. Only the data-fetching mechanism and indicator computation engine are replaced.
- **ADRs**: See `docs/adr/ADR-001.md` through `ADR-008.md` for architectural decisions made during the grilling session.
- **Glossary**: See `GLOSSARY.md` at repo root for domain terminology.
- **Windows ta-lib note**: Building ta-lib C library on Windows requires either `ta-lib-binary` wheel or Visual Studio build tools. If ta-lib installation fails, `pandas-ta` (pure Python) serves as immediate fallback with identical API surface.
