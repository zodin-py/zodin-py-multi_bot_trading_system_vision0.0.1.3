"""Order executor — ccxt order placement on Binance Testnet."""

from __future__ import annotations

import logging
import os
from typing import Optional

import ccxt

logger = logging.getLogger(__name__)


class OrderExecutor:
    """Places market and limit orders via ccxt on Binance Testnet."""

    def __init__(self, use_testnet: bool = True):
        self._use_testnet = use_testnet
        self._exchange = self._create_exchange()

    def _create_exchange(self) -> ccxt.binance:
        exchange = ccxt.binance({
            'apiKey': os.environ.get('BINANCE_API_KEY', ''),
            'secret': os.environ.get('BINANCE_SECRET_KEY', ''),
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        })
        if self._use_testnet:
            exchange.set_sandbox_mode(True)
        return exchange

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[dict]:
        """Place a market order. Returns order dict on success, None on failure."""
        try:
            order = self._exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=quantity,
            )
            logger.info(f"ccxt order placed: {order.get('id')} for {symbol} {side} {quantity}")
            return order
        except ccxt.BaseError as e:
            logger.error(f"ccxt order placement failed for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error placing ccxt order for {symbol}: {e}")
            return None

    def close_exchange(self) -> None:
        """Close exchange connection."""
        try:
            self._exchange.close()
        except Exception:
            pass
