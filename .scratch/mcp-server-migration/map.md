# Map: MCP Server Migration

Status: ready-for-agent
Date: 2026-10-19

## Notes

- Spec is at `spec.md` — the authoritative source of requirements
- All implementation issues are under `issues/` directory
- Triage state is recorded as a `Status:` line in each issue file
- Comments and conversation history append to the bottom of each file under `## Comments`
- Tickets are **vertical slices** — each cuts a complete path through all layers and is demoable on its own

## Decisions so far

- **ADR-001**: Data fetching via ccxt + DuckDB cache (replaces raw requests/websockets)
- **ADR-002**: Dual MCP + REST API architecture
- **ADR-003**: Python stack with ta-lib for indicators
- **ADR-004**: Dynamic SL/TP with 2:1 Risk-Reward ratio
- **ADR-005**: Configurable daily loss limit
- **ADR-006**: Automatic trade execution with safety mechanisms
- **ADR-007**: Hybrid data pipeline (REST + WebSocket + Cache)
- **ADR-008**: Timeframe configuration per analysis window
- **Issue tracker**: Local markdown under `.scratch/` (no GitHub CLI required)
- **Deployment**: Local Windows machine only
- **Vertical slices**: 7 tickets, each a complete end-to-end path

## Fog

- ta-lib C library build on Windows may require Visual Studio or `ta-lib-binary` wheel
- ccxt WebSocket subscription handling for Binance Testnet needs verification
- DuckDB integration with existing Flask app threading model needs design
- MCP stdio server lifecycle management alongside Flask/FastAPI servers

## Issues

| # | Title | Status | Blocked by |
|---|-------|--------|------------|
| 01 | Prefactoring — Data Layer Foundation | completed | None |
| 02 | Prefactoring — Indicator Layer | completed | 01 |
| 03 | Vertical Slice — Coin Analysis via MCP + REST | ready-for-agent | 01, 02 |
| 04 | Vertical Slice — Trade Execution with Dynamic SL/TP | ready-for-agent | 03 |
| 05 | Vertical Slice — Risk Management & Portfolio | ready-for-agent | 04 |
| 06 | Vertical Slice — Dashboard & Trade History | ready-for-agent | 03, 04, 05 |
| 07 | Backtest & Tests | ready-for-agent | 03, 04 |

## Comments