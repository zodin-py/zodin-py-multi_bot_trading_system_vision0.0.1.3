# Ticket 03: Wallet service + /api/wallet route

Status: ready-for-agent
Type: task
Created: 2026-10-25

## Problem

There is no dedicated wallet endpoint. The old Flask app has `/api/portfolio` and `/api/capital` but they depend on the executor (which is being removed). We need a clean Binance Spot wallet reader.

## Acceptance Criteria

- Create `backend/services/wallet_service.py` with a `WalletService` class
- Use Binance Spot Account API (requires API key from config, read-only)
- Fetch all balances, filter out zero-balance assets
- Convert each balance to USDT value using current market price
- Return format: `{balances:[{asset, free, locked, usdt_value}], total_usdt: number, timestamp: iso}`
- Add `GET /api/wallet` to the Flask app
- Add pytest tests

## API Contract

```
GET /api/wallet
→ {
    "balances": [
      {"asset": "BTC", "free": "0.5", "locked": "0.0", "usdt_value": 33716.25},
      {"asset": "USDT", "free": "1000.00", "locked": "0.0", "usdt_value": 1000.00}
    ],
    "total_usdt": 34716.25,
    "timestamp": "2026-10-25T10:30:00Z"
  }
```

## Implementation Notes

- Use ccxt with authenticated `binance()` instance (keys from config)
- `fetch_balance()` returns `{asset: {free, total}}` — derive locked from total - free
- For USDT conversion: fetch current price for each non-USDT asset via ccxt public endpoint
- If an asset price fetch fails, skip that asset's USDT conversion (don't fail the whole request)
- Mock ccxt in tests

## Tests

- `test_wallet_service_fetches_balances`: verifies structure with mocked response
- `test_wallet_service_total_usdt`: verifies total calculation
- `test_wallet_service_zero_balance_filtered`: verifies zero-balance assets are excluded
- `test_api_wallet_endpoint`: integration test via Flask test client
