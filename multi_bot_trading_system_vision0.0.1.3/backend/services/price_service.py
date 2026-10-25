"""Price service — fetches live price from Binance via ccxt public endpoint."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import ccxt

logger = logging.getLogger(__name__)


class PriceService:
    """Fetches live price for a trading pair via ccxt public endpoint."""

    _exchange: Optional[ccxt.binance] = None

    @property
    def exchange(self) -> ccxt.binance:
        if self._exchange is None:
            self._exchange = ccxt.binance({
                'enableRateLimit': True,
            })
        return self._exchange

    @staticmethod
    def _normalize_symbol(coin: str) -> str:
        """Normalize coin symbol: append /USDT if not present."""
        symbol_input = coin.strip().upper()
        if symbol_input.endswith('/USDT'):
            return symbol_input
        if not symbol_input.endswith('USDT'):
            return symbol_input + '/USDT'
        # Has USDT suffix but no slash - add slash
        return symbol_input[:-4] + '/' + symbol_input[-4:]

    def get_price_sync(self, coin: str) -> Dict[str, Any]:
        """Synchronous price fetch for Flask endpoints.

        Args:
            coin: Coin symbol without /USDT suffix, e.g. 'btc', 'eth'

        Returns:
            Dict with symbol, price, and timestamp, or error response.
        """
        full_symbol = self._normalize_symbol(coin)

        try:
            ticker = self.exchange.fetch_ticker(full_symbol)
            return {
                'symbol': full_symbol,
                'price': ticker.get('last', 0.0),
                'timestamp': datetime.fromtimestamp(
                    ticker.get('timestamp', 0) / 1000, tz=timezone.utc
                ).isoformat(),
            }
        except Exception as e:
            logger.warning(f'Price fetch failed for {full_symbol}: {e}')
            return {
                'error': 'Coin not found',
                'data': None,
            }


# Singleton for Flask app — created on first use
_price_service: Optional[PriceService] = None


def get_price_service() -> PriceService:
    global _price_service
    if _price_service is None:
        _price_service = PriceService()
    return _price_service