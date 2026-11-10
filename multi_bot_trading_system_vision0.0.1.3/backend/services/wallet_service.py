"""Wallet service — reads Binance Spot Account API."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

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
            # Check if API keys are configured
            if not config.BINANCE_API_KEY or not config.BINANCE_SECRET_KEY:
                raise ValueError(
                    'Binance API keys not configured. '
                    'Set TRADING_BINANCE_API_KEY and TRADING_BINANCE_SECRET_KEY in .env'
                )
            self._exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                },
            })
            self._exchange.set_sandbox_mode(config.USE_TESTNET)
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
            self.exchange.load_time_difference()
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
                        price_ticker = self.exchange.fetch_ticker(
                            f'{asset}/{config.DEFAULT_QUOTE}'
                        )
                        asset_price = price_ticker.get('last', 0.0)
                        usdt_value = (free + locked) * asset_price
                    except Exception as e:
                        # If price fetch fails, skip this asset's USDT conversion
                        # but still include the asset with usdt_value=0
                        logger.warning(f'Could not fetch price for {asset}: {e}')
                        usdt_value = 0.0

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

        except ValueError:
            raise
        except ccxt.AuthenticationError:
            logger.warning('Binance rejected wallet credentials or permissions')
            raise
        except Exception as e:
            logger.error('Wallet fetch failed: %s', type(e).__name__)
            return {
                'balances': [],
                'total_usdt': 0.0,
                'timestamp': datetime.now(tz=timezone.utc).isoformat(),
                'error': 'Wallet fetch failed',
            }
