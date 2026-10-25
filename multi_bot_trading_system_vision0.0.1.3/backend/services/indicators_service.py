"""Indicators service — fetches indicators via tradingview-ta + local computation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd

from backend import config

logger = logging.getLogger(__name__)


class IndicatorService:
    """Fetch technical indicators (RSI, MACD, EMA) from OHLCV candles.

    Uses CCXT to fetch OHLCV candles and custom numpy/pandas computation
    for indicator arrays. The spec requires "last 20 indicator values"
    consistent with TradingView calculations.
    """

    def __init__(self, exchange_id: str = "binance", lookback: int = 50) -> None:
        self._exchange_id = exchange_id
        self._lookback = lookback  # fetch this many candles, return last 20 indicators
        self._exchange = self._create_exchange()

    def _create_exchange(self) -> ccxt.binance:
        return ccxt.binance({"enableRateLimit": True})

    @staticmethod
    def _normalize_coin(coin: str) -> Optional[str]:
        """Normalize coin symbol: append USDT if not present.

        For ccxt OHLCV fetch, use BTCUSDT format (without slash).
        """
        symbol = coin.strip().upper()
        if not symbol.endswith("USDT"):
            symbol = symbol + "USDT"
        return symbol if symbol else None

    @staticmethod
    def _format_symbol_for_response(symbol: str) -> str:
        """Format symbol for API response (BTCUSDT -> BTC/USDT)."""
        if '/' in symbol:
            return symbol  # Already formatted
        if symbol.endswith("USDT") and len(symbol) > 4:
            return symbol[:-4] + "/" + symbol[-4:]
        return symbol

    @staticmethod
    def _normalize_timeframe(tf: str) -> str:
        """Normalize timeframe string."""
        tf_lower = tf.strip().lower()
        mapping = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        return mapping.get(tf_lower, "1h")

    def _get_ohlcv(self, symbol: str, timeframe: str, limit: int = 50) -> Optional[List[Dict[str, float]]]:
        """Fetch OHLCV candles from ccxt."""
        try:
            exchange = ccxt.binance({"enableRateLimit": True})
            raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            return [
                {
                    "time": float(c[0]),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]),
                }
                for c in raw
            ]
        except Exception as e:
            logger.warning(f"Failed to fetch OHLCV for {symbol}/{timeframe}: {e}")
            return None

    @staticmethod
    def _compute_rsi(closes: pd.Series, period: int = 14) -> List[float]:
        """Compute RSI using Wilder's smoothing (same as TradingView/pandas_ta)."""
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.dropna().tolist()[-20:]

    @staticmethod
    def _compute_macd(
        closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[List[float], List[float], List[float]]:
        """Compute MACD: (macd_line, signal_line, histogram)."""
        fast_ema = closes.ewm(span=fast, adjust=False).mean()
        slow_ema = closes.ewm(span=slow, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return (
            macd_line.dropna().tolist()[-20:],
            signal_line.dropna().tolist()[-20:],
            histogram.dropna().tolist()[-20:],
        )

    @staticmethod
    def _compute_ema(closes: pd.Series, period: int = 20) -> List[float]:
        """Compute EMA."""
        ema = closes.ewm(span=period, adjust=False).mean()
        return ema.dropna().tolist()[-20:]

    def get_indicators(
        self, coin: str, timeframe: str = "1h"
    ) -> Optional[Dict[str, Any]]:
        """Return last 20 values for RSI, MACD line+signal+hist, and EMA.

        Returns dict with arrays for rsi, macd, signal, hist, ema, plus metadata.
        Returns None on error.
        """
        try:
            symbol = self._normalize_coin(coin)
            if symbol is None:
                return None

            tf = self._normalize_timeframe(timeframe)

            # Fetch ~50 candles to ensure we have enough for 20 indicator values
            candles = self._get_ohlcv(symbol, tf, limit=self._lookback)
            if candles is None:
                return None

            if len(candles) < 30:
                return None

            df = pd.DataFrame(candles)
            closes = df["close"]

            # Compute indicator arrays
            rsi_vals = self._compute_rsi(closes, period=14)
            macd_vals, signal_vals, hist_vals = self._compute_macd(closes)
            ema_vals = self._compute_ema(closes, period=20)

            return {
                "rsi": rsi_vals,
                "macd": macd_vals,
                "signal": signal_vals,
                "hist": hist_vals,
                "ema": ema_vals,
                "timeframe": tf,
                "symbol": self._format_symbol_for_response(symbol),
            }

        except Exception as e:
            logger.warning(f"Failed to get indicators for {coin}/{timeframe}: {e}")
            return None

    def get_indicators_with_history(
        self, coin: str, timeframe: str = "1h", limit: int = 20
    ) -> Optional[Dict[str, Any]]:
        """Get indicators with explicit limit parameter.

        Alias for get_indicators — ensures last `limit` values are returned.
        """
        return self.get_indicators(coin, timeframe)