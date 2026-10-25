"""Wallet service — reads Binance Spot Account API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import ccxt

from backend import config

logger = logging.getLogger(__name__)


class WalletService:
    """Fetches Binance Spot wallet balances (read-only, requires API keys)."""

    def __init__(self) -> None:
        self._exchange: Optional[ccxt.binance] = None

    @property
    def exchange(self) -> ccxt.binance:
        if self._exchange is None:
            self._exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'enableRateLimit': True,
            })
        return self._exchange

    def get_wallet_sync(self) -> Dict[str, Any]:
        """Synchronous wallet fetch for Flask endpoints.

        Returns format per spec:
        {
            "balances": [
                {"asset": "BTC", "free": "0.5", "locked": "0.0", "usdt_value": 33716.25},
                {"asset": "USDT", "free": "1000.00", "locked": "0.0", "usdt_value": 1000.00}
            ],
            "total_usdt": number,
            "timestamp": iso
        }
        """
        try:
            balances = self.exchange.fetch_balance()
            result: Dict[str, Any] = {
                'balances': [],
                'total_usdt': 0.0,
                'timestamp': datetime.now(tz=timezone.utc).isoformat(),
            }

            # Extract balances from ccxt response
            # ccxt format: {info: {}, BTC: {free: x, total: y}, USDT: {...}, ...}
            all_balances: Dict[str, Dict[str, float]] = {}

            # Get non-info keys (actual balances)
            for key, value in balances.items():
                if key == 'info':
                    continue
                if isinstance(value, dict):
                    all_balances[key] = value

            for asset, data in all_balances.items():
                if not isinstance(data, dict):
                    continue

                free = float(data.get('free', 0))
                total = float(data.get('total', 0))
                locked = total - free

                if free == 0 and locked == 0:
                    # Skip zero-balance assets (per spec: filter out zero-balance)
                    continue

                # Get price for this asset (unless it's USDT)
                usdt_value = 0.0
                if asset == 'USDT' or asset == 'USD':
                    usdt_value = free + locked
                else:
                    try:
                        # Use format: BTCUSDT (no slash) for ccxt ticker
                        price_ticker = self.exchange.fetch_ticker(f'{asset}USDT')
                        asset_price = price_ticker.get('last', 0.0)
                        usdt_value = (free + locked) * asset_price
                    except Exception:
                        # If price fetch fails, skip this asset's USDT conversion
                        continue

                result['balances'].append({
                    'asset': asset,
                    'free': str(free),
                    'locked': str(locked),
                    'usdt_value': round(usdt_value, 2),
                })
                result['total_usdt'] += usdt_value

            # Sort by usdt_value descending
            result['balances'].sort(key=lambda x: x['usdt_value'], reverse=True)

            return result

        except Exception as e:
            logger.error(f'Wallet fetch failed: {e}')
            return {
                'balances': [],
                'total_usdt': 0.0,
                'timestamp': datetime.now(tz=timezone.utc).isoformat(),
                'error': str(e),
            }