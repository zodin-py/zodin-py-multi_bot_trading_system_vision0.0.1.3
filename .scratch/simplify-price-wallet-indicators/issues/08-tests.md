# Ticket 08: Tests for price, wallet, indicators

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

The three new services (price, wallet, indicators) need test coverage to ensure correct behavior and prevent regressions.

## Acceptance Criteria

- All tests in `tests/` directory follow existing pytest style
- External calls (ccxt, tradingview-ta) are mocked
- Tests cover:
  - Price service: valid coin, coin with USDT suffix, invalid coin, symbol normalization
  - Wallet service: balance fetch, USDT conversion, zero-balance filtering, total calculation
  - Indicators service: valid request, invalid coin, default timeframe, array lengths
  - API routes: HTTP status codes, response structure, error cases
- All tests pass: `pytest tests/ -v`

## Implementation Notes

- Use `pytest` with `unittest.mock.patch` for mocking
- Mock ccxt exchanges in price and wallet tests
- Mock tradingview-ta / pandas-ta in indicators tests
- Follow the style of existing tests in `tests/test_rsi_tradingview.py`
- Place tests in `multi_bot_trading_system_vision0.0.1.3/tests/`

## Test Structure

```
tests/
  test_price_service.py      # PriceService unit + route integration
  test_wallet_service.py     # WalletService unit + route integration
  test_indicators_service.py # IndicatorsService unit + route integration
  test_flask_app.py          # Flask app health, SPA serving, old routes gone
```
