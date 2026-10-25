# Ticket 02: Price service + /api/price route

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

There is no clean `/api/price` endpoint. The Flask app has `/api/load-coin` and `/api/indicators` but no dedicated price endpoint matching the spec contract.

## Acceptance Criteria

- Create `backend/services/price_service.py` with a `PriceService` class
- Use ccxt to fetch live price (public endpoint, no auth needed)
- Append `/USDT` to user input if not already present
- Return format: `{symbol: "BTC/USDT", price: number, timestamp: iso}`
- Error on invalid coin: `{error: "Coin not found", data: null}`
- Add `GET /api/price?coin=btc` to the Flask app
- Add pytest tests

## API Contract

```
GET /api/price?coin=btc
→ {
    "symbol": "BTC/USDT",
    "price": 67432.5,
    "timestamp": "2026-10-25T10:30:00Z"
  }

GET /api/price?coin=invalidcoin999
→ {
    "error": "Coin not found",
    "data": null
  }
```

## Implementation Notes

- Use `ccxt.binance()` for public price fetching
- Symbol format: input `btc` → internal `BTC/USDT` for ccxt, return `BTC/USDT`
- Timeframe is NOT needed for price (single current price)
- Mock ccxt in tests

## Tests (to create)

- `test_price_service_valid_coin`: verifies correct symbol and price structure
- `test_price_service_appends_usdt`: verifies `btc` → `BTC/USDT`
- `test_price_service_invalid_coin`: verifies error response
- `test_api_price_endpoint`: integration test via Flask test client