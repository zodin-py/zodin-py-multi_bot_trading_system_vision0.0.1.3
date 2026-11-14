"""Fetch personal Binance Spot fills for the configured trading pairs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import ccxt

from backend import config
from backend.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class BinanceCredentialsError(ValueError):
    """Raised when Binance API credentials are not configured."""


class TradeHistoryService:
    """Fetches real Spot account trades from Binance Live."""

    def get_trade_history_sync(self, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError('limit must be between 1 and 1000')
        if not config.BINANCE_API_KEY or not config.BINANCE_SECRET_KEY:
            raise BinanceCredentialsError(
                'Set TRADING_BINANCE_API_KEY and TRADING_BINANCE_SECRET_KEY in .env'
            )

        exchange = WalletService().exchange
        exchange.set_sandbox_mode(False)
        try:
            exchange.load_time_difference()
            trades = []
            quote = config.DEFAULT_QUOTE

            for configured_symbol in config.COINS:
                if not configured_symbol.endswith(quote):
                    raise ValueError(
                        f'Configured symbol {configured_symbol} does not use {quote}'
                    )
                symbol = f'{configured_symbol[:-len(quote)]}/{quote}'
                for trade in exchange.fetch_my_trades(symbol, limit=limit):
                    trades.append(self._format_trade(trade, symbol))

            trades.sort(key=lambda trade: trade['timestamp'], reverse=True)
            return trades[:limit]
        except ccxt.AuthenticationError:
            logger.warning('Binance rejected trade-history credentials or permissions')
            raise
        except Exception as error:
            logger.error('Binance trade-history fetch failed: %s', type(error).__name__)
            raise RuntimeError('Binance trade history could not be fetched') from error

    @staticmethod
    def _format_trade(trade: dict[str, Any], symbol: str) -> dict[str, Any]:
        trade_id = trade.get('id')
        side = trade.get('side')
        timestamp = trade.get('timestamp')
        price = trade.get('price')
        amount = trade.get('amount')

        if (
            trade_id is None
            or side not in ('buy', 'sell')
            or not isinstance(timestamp, (int, float))
            or not isinstance(price, (int, float))
            or not isinstance(amount, (int, float))
        ):
            raise RuntimeError(f'Binance returned an incomplete trade for {symbol}')

        fee = trade.get('fee')
        fee_data = None
        if isinstance(fee, dict) and fee.get('cost') is not None:
            fee_data = {
                'cost': float(fee['cost']),
                'currency': fee.get('currency') or '',
            }

        return {
            'id': f'{symbol}:{trade_id}',
            'symbol': trade.get('symbol') or symbol,
            'side': side,
            'price': float(price),
            'amount': float(amount),
            'cost': float(trade.get('cost') or float(price) * float(amount)),
            'timestamp': int(timestamp),
            'datetime': trade.get('datetime')
            or datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat(),
            'order': trade.get('order'),
            'fee': fee_data,
        }
