## Problem Statement
Das Projekt ist ein Multi-Bot Trading System mit Angular Frontend und hybridem Flask/FastAPI Backend. Der Code enthält Bots, Strategien, Backtest, Risk-Management, MCP-Integration, Caching und WebSocket. Für den aktuellen Bedarf wird nur Preisanzeige, Binance Spot-Wallet-Anzeige und Anzeige von Indikatoren benötigt. Der bestehende Code ist zu umfangreich, schwer verständlich und enthält viele ungenutzte Methoden/Klassen/Module. Das Frontend soll unverändert bleiben.

## Solution
Reduktion des Backends auf drei Domänen: Preis, Wallet, Indikatoren. Alles andere wird entfernt. Neue API-Routen /api/price, /api/wallet, /api/indicators werden eingeführt und per Mapping-Schicht an bestehende Routen gekoppelt. Config wird auf Minimum gekürzt. Daten werden live von Binance/public Endpoints und tradingview-ta geholt, kein Cache/WebSocket. Frontend Angular bleibt unangetastet, aber Komponenten die auf entfernten Backend-Features basieren werden gelöscht.

## User Stories
1. As a user, I want to search for an arbitrary coin by name, so that I can see its price without knowing the exact symbol format
2. As a user, I want the system to append /USDT to my coin input, so that the correct pair is queried
3. As a user, I want to see the current price of the selected coin, so that I can monitor market movements
4. As a user, I want the price to be fetched live on page load or button press, so that I always see fresh data
5. As a user, I want to see my Binance Spot Wallet with all coins, balances and USDT value, so that I can track my holdings
6. As a user, I want the total wallet value in USDT displayed, so that I have a quick overview of my portfolio value
7. As a user, I want the wallet to load automatically on page load, so that I immediately see my holdings
8. As a user, I want to select a timeframe, so that indicators match the view I am using
9. As a user, I want to see RSI values for the selected coin and timeframe, so that I can assess momentum
10. As a user, I want to see MACD values for the selected coin and timeframe, so that I can assess trend changes
11. As a user, I want to see EMA values for the selected coin and timeframe, so that I can assess moving averages
12. As a user, I want indicators to be read via tradingview-ta, so that calculation is consistent with TradingView
13. As a user, I want the last 20 indicator values returned, so that I can see recent history
14. As a user, I want a clear error message for invalid coins, so that I understand what went wrong
15. As a developer, I want the backend config to contain only Binance keys, default quote, timeframes and indicator parameters, so that the system stays minimal
16. As a developer, I want no WebSocket or DuckDB cache, so that the system stays simple and live
17. As a developer, I want old API routes to be mapped or removed cleanly, so that the Angular frontend does not break unexpectedly
18. As a developer, I want unused modules removed, so that the codebase stays understandable
19. As a developer, I want frontend components depending on removed backend features deleted, so that dead code does not remain
20. As an operator, I want Binance API keys to stay server-side and read-only, so that credentials are not exposed

## Implementation Decisions
- Scope: Only Preis, Wallet, Indikatoren remain. All other domains removed.
- Coin search: user input without /USDT, backend appends /USDT. Fallback not required.
- Price source: ccxt REST public endpoints, live on request.
- Wallet source: Binance Spot account API with existing keys from .env, read-only. Balances converted to USDT via current prices.
- Indicators source: tradingview-ta library for RSI, MACD, EMA. No local calculation.
- Timeframe: indicators depend on timeframe selected in UI.
- API contracts:
  * GET /api/price?coin=btc → {symbol: "BTC/USDT", price: number, timestamp: iso}
  * GET /api/wallet → {balances:[{asset, free, locked, usdt_value}], total_usdt: number, timestamp: iso}
  * GET /api/indicators?coin=btc&tf=1h → {rsi:[...20], macd:[...20], ema:[...20], timeframe, symbol}
- Mapping layer: old routes are mapped to new routes or removed. Mapping exists only for routes still referenced by Angular.
- Error handling: invalid coin → {error:"Coin not found", data:null}
- Config minimalization: keep BINANCE_API_KEY, BINANCE_SECRET_KEY, DEFAULT_QUOTE=USDT, TIMEFRAMES, indicator parameters.
- No cache/WebSocket: remove data/cache, market_data websocket, ws_stream, repository.
- Removal list: execution, trades, portfolio except wallet read, risk, analysis, strategies, old indicator bots, bots, aggregator, mcp_integration, cache, websocket parts.
- Frontend cleanup: remove components for bot-signals, open-trades, risk-management, trade-history, capital/open-trades/signal cards where they depend on removed backend.

## Testing Decisions
- Good test: verify external behavior via API contracts, not internal implementation.
- Test seams: API layer is highest seam. Tests call /api/price, /api/wallet, /api/indicators with mocked ccxt and Binance responses.
- Modules tested: price_service, wallet_service, indicators_service, API routes.
- Prior art: existing pytest tests for backend services. Use same style.
- Mock external calls to Binance and tradingview-ta to keep tests deterministic.

## Out of Scope
- Trading execution, order placement, SL/TP, position sizing
- Risk management, daily loss limits, cooldowns
- Backtesting, strategy bots, signal aggregation
- MCP server integration
- Caching, WebSocket real-time streaming
- New frontend features or redesign of Angular UI
- Multi-coin portfolio management beyond current wallet view
- Historical price charts beyond last 20 indicator values

## Further Notes
- Frontend Angular bleibt unangetastet in Struktur, aber tote Komponenten werden entfernt.
- Sprache der UI bleibt Deutsch.
- Aktualisierung nur beim Laden der Seite oder per Button, kein Auto-Refresh.
- API Keys liegen bereits in multi_bot_trading_system_vision0.0.1.3/.env.
