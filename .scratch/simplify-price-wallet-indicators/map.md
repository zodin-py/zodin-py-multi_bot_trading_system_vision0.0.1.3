# Map: Simplify Price, Wallet, Indicators

Status: resolved
Date: 2026-10-25

## Notes

- Spec is at `.scratch/simplify-price-wallet-indicators/spec.md` — the authoritative source of requirements
- All implementation issues are under `.scratch/simplify-price-wallet-indicators/issues/`
- Triage state is recorded as a `Status:` line in each issue file
- Comments and conversation history append to the bottom of each file under `## Comments`

## Decisions so far

- **Scope**: Backend reduced to three domains — Price, Wallet, Indicators
- **Price source**: ccxt REST public endpoints (live on request)
- **Wallet source**: Binance Spot Account API with existing keys from `.env`, read-only
- **Indicators source**: ccxt + pandas-ta — candles fetched from exchange, indicators computed locally (tradingview-ta only returns single-point values, cannot provide 20-value series)
- **Timeframe**: indicators depend on UI-selected timeframe
- **API contracts**:
  - `GET /api/price?coin=btc` → `{symbol: "BTC/USDT", price: number, timestamp: iso}`
  - `GET /api/wallet` → `{balances:[{asset, free, locked, usdt_value}], total_usdt: number, timestamp: iso}`
  - `GET /api/indicators?coin=btc&tf=1h` → `{rsi:[...20], macd:[...20], signal:[...20], hist:[...20], ema:[...20], timeframe, symbol}`
- **No cache/WebSocket**: remove data/cache, market_data websocket, ws_stream, repository
- **Frontend**: Angular stays structurally unchanged; dead components (bot-signals, open-trades, risk-management, trade-history, capital/open-trades/signal KPI cards) deleted
- **Language**: UI stays German
- **Error handling**: invalid coin → `{error:"Coin not found", data:null}`

## Issues

| # | Title | Status | Blocked by |
|---|-------|--------|------------|
| 01 | Reduce config to minimum | resolved | None |
| 02 | Price service + /api/price route | resolved | None |
| 03 | Wallet service + /api/wallet route | resolved | None |
| 04 | Indicators service + /api/indicators route | resolved | None |
| 05 | Minimal Flask app serving Angular | resolved | 02, 03, 04 |
| 06 | Remove unused backend modules | resolved | 05 |
| 07 | Frontend component cleanup | resolved | 05 |
| 08 | Tests for price, wallet, indicators | resolved | 02, 03, 04 |

## Comments