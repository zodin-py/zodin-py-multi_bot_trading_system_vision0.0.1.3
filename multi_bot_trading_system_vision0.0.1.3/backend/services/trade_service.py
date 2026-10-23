# filepath: services/trade_service.py
"""
Trade Service — coordinates MarketData + Executor for real trade execution.

Responsibilities:
- Fetch current price and S/R levels from the provider
- Compute dynamic SL/TP
- Place orders via ccxt on Binance Testnet
- Track position state and daily P&L
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.bots.base_bot import SignalType
from backend.config import COINS, USE_TESTNET
from backend.data.market_data import MarketData
from backend.execution.executor import Trade, TradeExecutor
from backend.indicators.provider import IndicatorProvider

logger = logging.getLogger(__name__)


class TradeService:
    """Service that bridges analysis and execution."""

    def __init__(
        self,
        market_data: MarketData,
        executor: TradeExecutor,
        provider: IndicatorProvider,
    ):
        self.market_data = market_data
        self.executor = executor
        self.provider = provider

    # ------------------------------------------------------------------
    # Open a trade
    # ------------------------------------------------------------------

    def open_trade(
        self,
        symbol: str,
        timeframe: str,
        signal: SignalType,
    ) -> Optional[Dict[str, Any]]:
        """
        Open a trade for the given symbol/timeframe/signals.

        Steps:
        1. Fetch current price from MarketData
        2. Get S/R levels from SRBot via provider
        3. Compute dynamic SL/TP
        4. Place real order via ccxt
        5. Record trade in executor
        """
        try:
            # Normalise symbol
            norm_symbol = self._normalize(symbol)
            if norm_symbol not in COINS:
                raise ValueError(f"Unsupported symbol: {symbol}")

            # Get current price
            current_price = self.market_data.get_current_price(norm_symbol)
            if current_price <= 0:
                logger.warning(f"No price available for {norm_symbol}")
                return {'error': f'No price data for {norm_symbol}'}

            # Get indicators for S/R levels and ATR
            indicators = self.provider.get_indicators(norm_symbol, timeframe)
            if indicators is None:
                return {'error': 'No indicator data available'}

            support_levels = indicators.get('support_levels', [])
            resistance_levels = indicators.get('resistance_levels', [])
            atr = indicators.get('atr', 0.0)

            # Open the trade via executor
            trade = self.executor.open_trade(
                symbol=norm_symbol,
                timeframe=timeframe,
                signal=signal,
                entry_price=current_price,
                support_levels=support_levels,
                resistance_levels=resistance_levels,
                atr=atr,
            )

            if trade is None:
                return {'error': 'Failed to open trade (check logs)'}

            return trade.to_dict()

        except Exception as e:
            logger.error(f"Error opening trade: {e}")
            return {'error': str(e)}

    # ------------------------------------------------------------------
    # Close a trade
    # ------------------------------------------------------------------

    def close_trade(self, trade_id: str, reason: str = 'manual') -> Optional[Dict[str, Any]]:
        """Close an open trade at the current market price."""
        try:
            trade = self.executor.open_trades.get(trade_id)
            if trade is None:
                return {'error': f'Trade {trade_id} not found'}

            current_price = self.market_data.get_current_price(trade.symbol)
            result = self.executor.close_trade(trade_id, reason=reason, current_price=current_price)
            if result is None:
                return {'error': 'Failed to close trade'}

            return result.to_dict()

        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            return {'error': str(e)}

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_open_trades(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.executor.get_open_trades()]

    def get_trade_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        trades = self.executor.get_trade_history(start, end)
        stats = self.executor.get_performance_stats(start, end)
        return {
            'trades': [t.to_dict() for t in trades],
            'stats': stats,
        }

    def get_portfolio(self) -> Dict[str, Any]:
        return self.executor.get_portfolio()

    # ------------------------------------------------------------------
    # Daily loss control
    # ------------------------------------------------------------------

    def is_trading_halted(self) -> bool:
        return self.executor._check_daily_loss_limit()

    def reset_daily_loss(self) -> bool:
        self.executor._daily_reset_date = None  # force reset on next check
        self.executor.daily_pnl = 0.0
        self.executor._trades_closed_today = []
        logger.info("Daily P&L manually reset")
        return True

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(symbol: str) -> str:
        s = symbol.upper().strip()
        return s if s.endswith('USDT') else f"{s}USDT"


# Singleton
_trade_service: Optional[TradeService] = None


def get_trade_service() -> TradeService:
    global _trade_service
    if _trade_service is None:
        raise RuntimeError("TradeService not initialized — call init_trade_service() first")
    return _trade_service


def init_trade_service(market_data: MarketData, executor: TradeExecutor, provider: IndicatorProvider) -> TradeService:
    global _trade_service
    _trade_service = TradeService(market_data, executor, provider)
    return _trade_service
