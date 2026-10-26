"""Indicators service — fetches indicators via ccxt REST (OHLCV candles needed)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import ccxt
import pandas as pd

from backend import config

logger = logging.getLogger(__name__)


class IndicatorService:
    """Fetch technical indicators (RSI, MACD, EMA) from OHLCV candles.

    Uses CCXT to fetch OHLCV candles (50 most recent) and computes
    indicator arrays locally via pandas.
    """

    def __init__(self, lookback: int = 50) -> None:
        self._lookback = lookback
        # RSI parameters come from config (length + source), e.g. length=14, source=close
        self._rsi_params: Dict[str, Any] = dict(config.INDICATOR_PARAMS.get('rsi', {}))
        self._rsi_length: int = int(self._rsi_params.get('length', 14))
        self._rsi_source: str = str(self._rsi_params.get('source', 'close')).strip().lower()

    @staticmethod
    def _normalize_coin(coin: str) -> Optional[str]:
        """Normalize coin symbol to BTC/USDT format."""
        symbol = coin.strip().upper()
        if symbol.endswith('/USDT'):
            return symbol
        if not symbol.endswith('USDT'):
            return symbol + 'USDT'
        return symbol[:-4] + '/USDT'

    @staticmethod
    def _format_symbol_for_response(symbol: str) -> str:
        """Format symbol for API response (BTCUSDT -> BTC/USDT)."""
        if '/' in symbol:
            return symbol
        if symbol.endswith("USDT") and len(symbol) > 4:
            return symbol[:-4] + "/" + symbol[-4:]
        return symbol

    @staticmethod
    def _normalize_timeframe(tf: str) -> str:
        """Normalize timeframe string."""
        tf_lower = tf.strip().lower()
        mapping = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        return mapping.get(tf_lower, "1h")

    def get_indicators(self, coin: str, timeframe: str = "1h") -> Optional[Dict[str, Any]]:
        """Return last 20 values for RSI, MACD, EMA.

        Returns dict with arrays for rsi, macd, signal, hist, ema, plus metadata.
        """
        try:
            symbol = self._normalize_coin(coin)
            if symbol is None:
                return None

            tf = self._normalize_timeframe(timeframe)

            # Fetch ~50 candles
            exchange = ccxt.binance({'enableRateLimit': True, 'timeout': 20000, 'options': {'defaultType': 'spot'}})
            try:
                raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=self._lookback)
            except Exception:
                # Retry with bybit as fallback
                import ccxt as ccxt2
                bybit = ccxt2.bybit({'enableRateLimit': True, 'timeout': 20000})
                raw = bybit.fetch_ohlcv(symbol, timeframe=timeframe, limit=self._lookback)

            if len(raw) < 30:
                return None

            # Compute indicators — RSI uses the configured length + source
            closes = self._extract_source_series(raw)
            df = pd.DataFrame({"close": closes})

            # Compute indicators
            rsi_vals = self._compute_rsi(df["close"], period=self._rsi_length)
            macd_vals, signal_vals, hist_vals = self._compute_macd(df["close"])
            ema_vals = self._compute_ema(df["close"])

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

    @staticmethod
    def _extract_source_series(raw: List[List[float]], source: str = "close") -> List[float]:
        """Extract the price series for the configured RSI source from OHLCV candles.

        OHLCV column order: [timestamp, open, high, low, close, volume].
        Default source is 'close' (TradingView default for RSI).
        """
        source_map = {
            "open": 1,
            "high": 2,
            "low": 3,
            "close": 4,
        }
        idx = source_map.get(source, 4)
        return [float(c[idx]) for c in raw]

    @staticmethod
    def _compute_rsi(closes: pd.Series, period: int = 14) -> List[float]:
        """Compute RSI using Wilder's smoothing."""
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
