"""TradingView provider — fetches indicators from TradingView via tradingview-ta."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from tradingview_ta import TA_Handler

from backend.domains.indicators.models import IndicatorValues

logger = logging.getLogger(__name__)


class IndicatorProvider:
    """Protocol: any indicator provider must implement get_indicators()."""

    async def get_indicators(self, symbol: str, timeframe: str) -> Optional[IndicatorValues]:
        """Fetch indicator values for symbol/timeframe. Returns None on failure."""
        raise NotImplementedError


class TradingViewProvider(IndicatorProvider):
    """Fetches technical indicators from TradingView using tradingview-ta."""

    _TIMEFRAME_MAP = {
        '1m': '1', '1 min': '1',
        '5m': '5', '5 min': '5',
        '15m': '15', '15 min': '15',
        '30m': '30', '30 min': '30',
        '1h': '60', '1 hour': '60',
        '4h': '240', '4 hour': '240',
        '1d': 'D', '1 day': 'D',
        '1w': 'W', '1 week': 'W',
    }

    def __init__(
        self,
        screener: str = 'crypto',
        exchange: str = 'BINANCE',
        timeout: float = 10.0,
    ) -> None:
        self._screener = screener
        self._exchange = exchange
        self._timeout = timeout

    def _normalize_timeframe(self, timeframe: str) -> str:
        tf = timeframe.strip().lower()
        return self._TIMEFRAME_MAP.get(tf, timeframe.strip())

    async def get_indicators(self, symbol: str, timeframe: str) -> Optional[IndicatorValues]:
        try:
            normalized_tf = self._normalize_timeframe(timeframe)
            handler = TA_Handler(
                symbol=symbol,
                exchange=self._exchange,
                screener=self._screener,
                interval=normalized_tf,
                timeout=self._timeout,
            )
            result = handler.get_analysis()
            return self._parse_result(result, symbol, timeframe)
        except Exception as e:
            logger.warning(f'TradingView fetch failed for {symbol}/{timeframe}: {e}')
            return None

    def _parse_result(self, result: Any, symbol: str, timeframe: str) -> Optional[IndicatorValues]:
        try:
            td = result.indicators
            iv = IndicatorValues(
                symbol=symbol,
                timeframe=timeframe,
                timestamp_ms=int(result.timestamp * 1000),
            )

            # Direct field mapping
            direct = {
                'RSI': 'rsi',
                'MACD': 'macd',
                'MACD Signal': 'macd_signal',
                'MACD Histogram': 'macd_hist',
                'ADX': 'adx',
                '+DI': 'plus_di',
                '-DI': 'minus_di',
                'ATR': 'atr',
            }
            for tv_key, field in direct.items():
                val = td.get(tv_key)
                if val is not None:
                    try:
                        setattr(iv, field, float(val))
                    except (TypeError, ValueError):
                        pass

            # EMAs/SMAs with period suffix
            for key, val in td.items():
                if val is None:
                    continue
                try:
                    fval = float(val)
                except (TypeError, ValueError):
                    continue
                if key.startswith('EMA.'):
                    period = key[4:]
                    if period == '9':
                        iv.ema_9 = fval
                    elif period == '21':
                        iv.ema_21 = fval
                    elif period == '50':
                        iv.ema_50 = fval
                    elif period == '200':
                        iv.ema_200 = fval
                elif key.startswith('SMA.'):
                    period = key[4:]
                    if period == '20':
                        iv.sma_20 = fval
                    elif period == '50':
                        iv.sma_50 = fval
                elif '%K' in key or 'Stoch.K' in key:
                    iv.stoch_k = fval
                elif '%D' in key or 'Stoch.D' in key:
                    iv.stoch_d = fval
                elif 'BB.lower' in key or 'BB.Lower' in key:
                    iv.bb_lower = fval
                elif 'BB.upper' in key or 'BB.Upper' in key:
                    iv.bb_upper = fval
                elif 'BB.middle' in key or 'BB.Middle' in key:
                    iv.bb_middle = fval
                elif 'CCI' in key:
                    iv.cci = fval
                elif 'Mom' in key:
                    iv.momentum = fval

            # OHLCV raw price
            iv.close = float(td.get('close', 0))
            iv.open = float(td.get('open', 0))
            iv.high = float(td.get('high', 0))
            iv.low = float(td.get('low', 0))
            iv.volume = float(td.get('volume', 0))
            iv.candle_count = int(td.get('volume', 0))

            return iv
        except Exception as e:
            logger.warning(f'Failed to parse TradingView result for {symbol}: {e}')
            return None
