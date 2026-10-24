# Wayfinder Map: Backend Restructure

## Destination

Transform the monolithic backend into a clean, domain-driven modular structure with FastAPI + Angular Dev Server launcher. All indicators calculated locally via pluggable `IndicatorProvider` protocol. 7 bots split into `indicators` (RSI, MACD, MFI) + `strategies` (SR, SMC, Harmonic, Trend). Dependency Injection Container replaces global singletons.

## Notes

- **Skills to consult**: domain-modeling, wayfinder, prototype (for launcher/DI container)
- **Current stack**: FastAPI (8000), MCP (8001), Angular Dev (4200)
- **Config**: `config.py` stays global; feature-specific constants move into domain
- **No Flask** — removed entirely
- **Launcher**: `python launcher.py` starts FastAPI + `ng serve` (dev), `--prod` serves build later
- **Indicators Source**: `tradingview-ta` (TradingView scrape) for RSI, MACD, Stoch, ADX, EMAs, SMAs, BB, Pivots, etc. — wrapped behind `IndicatorProvider` protocol. MFI, ATR fallback local calc.
- **Strategies**: SR, SMC, Harmonic, Trend remain local pattern recognition

## Decisions so far

- [x] **Single Command Launcher**: FastAPI (8000) + Angular Dev Server (4200) parallel, 1-3s delay
- [x] **Domain Structure**: data, indicators, strategies, analysis, execution, trades, portfolio, risk, api
- [x] **DI Container**: Constructor injection, no singletons
- [x] **Indicators via tradingview-ta**: `tradingview-ta` (TradingView scrape) for RSI, MACD, Stoch, ADX, EMAs, SMAs, BB, Pivots, etc. — wrapped behind `IndicatorProvider` protocol. MFI, ATR fallback local calc.
- [x] **Bots Split**: 3 indicator-bots → `indicators/`, 4 strategy-bots → `strategies/`
- [x] **Wayfinder Map as Markdown**: Saved to `.scratch/backend-restructure/wayfinder-map.md`
- [x] **Glossary Correction**: SR, SMC, Harmonic, Trend → Strategies (not indicators)
- [x] **Tickets Created**: 14 child tickets in `.scratch/backend-restructure/issues/` (see below)

## Tickets (Child Issues)

| # | Title | Blocked By |
|---|-------|------------|
| 01 | Launcher + Dev Server | — |
| 02 | DI Container | — |
| 03 | Domain Structure Skeleton | — |
| 04 | Data Domain Split | 03 |
| 05 | Indicators Domain | 03, 02 |
| 06 | Strategies Domain | 03, 05 |
| 07 | Analysis Service Refactor | 05, 06, 02 |
| 08 | Execution Domain Split | 03, 02 |
| 09 | Trades Domain | 08, 07 |
| 10 | Portfolio & Risk Domain | 08, 09 |
| 11 | API Routes Split | 07, 09, 10, 02 |
| 12 | MCP Integration Refactor | 02, 07, 09 |
| 13 | Config Cleanup | 02 |
| 14 | Integration Verification | 11, 12, 13 |

**Frontier** (open, unblocked): 01, 02, 03

## Not yet specified

- **MFI/ATR Local Fallback**: `tradingview-ta` has no MFI/ATR → implement local calculation as fallback in `IndicatorProvider`
- **Online Indicator Source Reliability**: TradingView scrape is unofficial — rate limits, breaking changes risk. Monitor or add caching layer.
- **MCP Integration**: Whether `mcp_integration/server.py` moves into `domains/api/mcp/` or stays top-level
- **Tests Structure**: How test files mirror domain structure (`tests/domains/...`)
- **Config Validation**: Pydantic Settings for `config.py` with env validation
- **Error Handling**: Centralized exception handlers in FastAPI
- **Logging**: Structured logging setup per domain
- **Database/Migrations**: If DuckDB schema changes needed for new trade/portfolio models
- **OpenAPI/Swagger**: Grouping tags per domain in API docs

## Out of scope

- **Production Angular Build**: `--prod` launcher mode deferred until `dist/angular/` exists
- **WebSocket Push to Frontend**: Current polling from Angular sufficient; SSE/WebSocket later
- **Authentication/Authorization**: Not in current scope
- **Multi-Exchange Support**: Binance-only for now
- **Backtesting Engine**: Separate effort
- **Docker/Deployment**: Out of restructure scope