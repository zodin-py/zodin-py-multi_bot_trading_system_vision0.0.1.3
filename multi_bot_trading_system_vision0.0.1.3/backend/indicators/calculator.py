# filepath: indicators/calculator.py
"""
Indicator Calculator — zentraler Engine für alle technischen Indikatoren.

- Berechnet vectorisiert über pandas_ta (primary) oder ta-lib (fallback)
  RSI, MACD, MFI, ADX, ATR, SMA, EMA
- Cacht Ergebnisse pro (symbol, timeframe, params_hash)
- Bietet inkrementelles Update bei neuen geschlossenen Kerzen
- Liefert ein einheitliches Dict pro (symbol, timeframe) zurück, das alle Bots
  gemeinsam nutzen können

Standard-Parametrisierung (TradingView-kompatibel):
  RSI(14), MACD(12,26,9), MFI(14), ADX(14), ATR(14), SMA(20/50), EMA(9/21/50/200)
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


logger = logging.getLogger(__name__)

try:
    import pandas_ta as pta  # type: ignore[import-not-found]
except ImportError:
    try:
        import pandas_ta_classic as pta
    except ImportError:
        pta = None  # type: ignore[assignment]

try:
    import talib  # type: ignore[import-not-found]
except Exception:
    talib = None  # type: ignore[assignment]


# ---------- Standard-Parametrisierung ----------
_DEFAULTS = {
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'mfi_period': 14,
    'adx_period': 14,
    'atr_period': 14,
    'sma_periods': [20, 50],
    'ema_periods': [9, 21, 50, 200],
}


def _hash_params(params: Dict[str, Any]) -> str:
    h = hashlib.md5()
    h.update(str(sorted(params.items())).encode())
    return h.hexdigest()[:12]


# ---------- Data class für Indikator-Werte ----------

@dataclass
class IndicatorValues:
    """Ein Snapshot der neuesten Indikatorwerte + Metadaten."""
    symbol: str
    timeframe: str
    timestamp_ms: int
    params_hash: str
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    mfi: float
    adx: float
    plus_di: float
    minus_di: float
    atr: float
    ema_9: float
    ema_21: float
    ema_50: float
    ema_200: float
    sma_20: float
    sma_50: float
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rsi': self.rsi,
            'macd': self.macd,
            'macd_signal': self.macd_signal,
            'macd_hist': self.macd_hist,
            'mfi': self.mfi,
            'adx': self.adx,
            'plus_di': self.plus_di,
            'minus_di': self.minus_di,
            'atr': self.atr,
            'ema_9': self.ema_9,
            'ema_21': self.ema_21,
            'ema_50': self.ema_50,
            'ema_200': self.ema_200,
            'sma_20': self.sma_20,
            'sma_50': self.sma_50,
            'timestamp_ms': self.timestamp_ms,
            'params_hash': self.params_hash,
        } | self.extra


# ---------- Der Calculator ----------

class IndicatorCalculator:
    """
    Berechnet technische Indikatoren vectorisiert und cacht sie.

    Beispiel:
        calc = IndicatorCalculator()
        values = calc.compute_from_candles('BTCUSDT', '1h', candles)
        values.to_dict() -> { 'rsi': ..., 'macd': ..., ... }
    """

    def __init__(self, defaults: Optional[Dict[str, Any]] = None):
        self._defaults = {**_DEFAULTS, **(defaults or {})}
        self._cache: Dict[str, IndicatorValues] = {}  # key -> IndicatorValues

    # ---------- Public API ----------

    def compute(
        self,
        symbol: str,
        timeframe: str,
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[IndicatorValues]:
        """Berechne alle Indikatoren und cachte Ergebnis."""
        if len(closes) < self._min_required():
            return None

        params = params or {}
        merged = {**self._defaults, **params}
        params_hash = _hash_params(merged)
        key = f"{symbol}:{timeframe}:{params_hash}"

        cached = self._cache.get(key)
        if cached is not None and cached.extra.get('candle_count') == len(closes):
            return cached

        try:
            result = self._compute_internal(symbol, timeframe, opens, highs, lows, closes, volumes, merged)
        except Exception as e:
            logger.error(f"Indicator computation failed for {symbol} {timeframe}: {e}")
            return None

        result.extra['candle_count'] = len(closes)
        self._cache[key] = result
        return result

    def compute_from_candles(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Dict[str, Any]],
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[IndicatorValues]:
        """Hilfsfunktion: nimmt fertige Candle-Dicts."""
        if not candles:
            return None
        opens = [c['open'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        volumes = [c['volume'] for c in candles]
        return self.compute(symbol, timeframe, opens, highs, lows, closes, volumes, params)

    def get_cached(self, symbol: str, timeframe: str) -> Optional[IndicatorValues]:
        """Hole gecachte Werte ohne Neu-Berechnung."""
        prefix = f"{symbol}:{timeframe}:"
        matches = [v for k, v in self._cache.items() if k.startswith(prefix)]
        if not matches:
            return None
        return max(matches, key=lambda v: v.extra.get('candle_count', 0))

    def incrementally_update(
        self,
        symbol: str,
        timeframe: str,
        old_candles: List[Dict[str, Any]],
        new_candle: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[IndicatorValues]:
        candles = list(old_candles) + [new_candle]
        return self.compute_from_candles(symbol, timeframe, candles, params)

    def invalidate(self, symbol: str, timeframe: str) -> None:
        prefix = f"{symbol}:{timeframe}:"
        for key in list(self._cache.keys()):
            if key.startswith(prefix):
                del self._cache[key]

    def clear_cache(self):
        self._cache.clear()

    # ---------- Intern ----------

    def _min_required(self) -> int:
        return max(
            self._defaults['rsi_period'],
            self._defaults['macd_slow'],
            self._defaults['mfi_period'],
            self._defaults['adx_period'],
            self._defaults['atr_period'],
            max(self._defaults['ema_periods']) if self._defaults['ema_periods'] else 0,
            max(self._defaults['sma_periods']) if self._defaults['sma_periods'] else 0,
        ) + 5

    def _compute_internal(
        self,
        symbol: str,
        timeframe: str,
        opens,
        highs,
        lows,
        closes,
        volumes,
        params: Dict[str, Any],
    ) -> IndicatorValues:
        df = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': volumes})

        if talib is not None:
            # ---------- ta-lib (faster, C-backed) ----------
            close_s = pd.Series(closes)
            high_s = pd.Series(highs)
            low_s = pd.Series(lows)
            volume_s = pd.Series(volumes)
            period = params['rsi_period']
            rsi_val = float(talib.RSI(close_s.values, timeperiod=period)[-1])
            macd, macd_signal, macd_hist = talib.MACD(
                close_s.values,
                fastperiod=params['macd_fast'],
                slowperiod=params['macd_slow'],
                signalperiod=params['macd_signal'],
            )
            macd_val = float(macd[-1])
            macd_signal_val = float(macd_signal[-1])
            macd_hist_val = float(macd_hist[-1])
            mfi_val = float(talib.MFI(high_s.values, low_s.values, close_s.values, volume_s.values, timeperiod=params['mfi_period'])[-1])
            adx_val = float(talib.ADX(high_s.values, low_s.values, close_s.values, timeperiod=params['adx_period'])[-1])
            plus_di = float(talib.PLUS_DI(high_s.values, low_s.values, close_s.values, timeperiod=params['adx_period'])[-1])
            minus_di = float(talib.MINUS_DI(high_s.values, low_s.values, close_s.values, timeperiod=params['adx_period'])[-1])
            atr_val = float(talib.ATR(high_s.values, low_s.values, close_s.values, timeperiod=params['atr_period'])[-1])
            ema_vals = [float(talib.EMA(close_s.values, timeperiod=p)[-1]) for p in params['ema_periods']]
            sma_vals = [float(talib.SMA(close_s.values, timeperiod=p)[-1]) for p in params['sma_periods']]
            ema_9, ema_21, ema_50, ema_200 = (
                ema_vals[0] if len(ema_vals) > 0 else closes[-1],
                ema_vals[1] if len(ema_vals) > 1 else closes[-1],
                ema_vals[2] if len(ema_vals) > 2 else closes[-1],
                ema_vals[3] if len(ema_vals) > 3 else closes[-1],
            )
            sma_20, sma_50 = (
                sma_vals[0] if len(sma_vals) > 0 else closes[-1],
                sma_vals[1] if len(sma_vals) > 1 else closes[-1],
            )
        elif pta is not None:
            # ---------- pandas_ta (pure Python fallback) ----------
            close_s = df['close']
            high_s = df['high']
            low_s = df['low']
            volume_s = df['volume']
            period = params['rsi_period']
            rsi_val = float(pta.rsi(close_s, length=period).iloc[-1])
            macd_df = pta.macd(close_s, fast=params['macd_fast'], slow=params['macd_slow'], signal=params['macd_signal'])
            macd_key = f"MACD_{params['macd_fast']}_{params['macd_slow']}_{params['macd_signal']}"
            macd_signal_key = f"MACDs_{params['macd_fast']}_{params['macd_slow']}_{params['macd_signal']}"
            macd_hist_key = f"MACDh_{params['macd_fast']}_{params['macd_slow']}_{params['macd_signal']}"
            macd_val = float(macd_df[macd_key].iloc[-1])
            macd_signal_val = float(macd_df[macd_signal_key].iloc[-1])
            macd_hist_val = float(macd_df[macd_hist_key].iloc[-1])
            mfi_val = float(pta.mfi(high_s, low_s, close_s, volume_s, length=period).iloc[-1])
            adx_df = pta.adx(high_s, low_s, close_s, length=period)
            adx_val = float(adx_df[f'ADX_{period}'].iloc[-1])
            plus_di = float(adx_df[f'DMP_{period}'].iloc[-1])
            minus_di = float(adx_df[f'DMN_{period}'].iloc[-1])
            atr_val = float(pta.atr(high_s, low_s, close_s, length=params['atr_period']).iloc[-1])
            ema_9 = float(pta.ema(close_s, length=9).iloc[-1])
            ema_21 = float(pta.ema(close_s, length=21).iloc[-1])
            ema_50 = float(pta.ema(close_s, length=50).iloc[-1])
            ema_200 = float(pta.ema(close_s, length=200).iloc[-1]) if len(close_s) >= 200 else closes[-1]
            sma_20 = float(pta.sma(close_s, length=20).iloc[-1])
            sma_50 = float(pta.sma(close_s, length=50).iloc[-1])
        else:
            raise RuntimeError("Keine Indikator-Bibliothek verfügbar (pandas_ta / ta-lib)")

        return IndicatorValues(
            symbol=symbol,
            timeframe=timeframe,
            timestamp_ms=int(time.time() * 1000),
            params_hash=_hash_params(params),
            rsi=rsi_val,
            macd=macd_val,
            macd_signal=macd_signal_val,
            macd_hist=macd_hist_val,
            mfi=mfi_val,
            adx=adx_val,
            plus_di=plus_di,
            minus_di=minus_di,
            atr=atr_val,
            ema_9=ema_9,
            ema_21=ema_21,
            ema_50=ema_50,
            ema_200=ema_200,
            sma_20=sma_20,
            sma_50=sma_50,
        )

    def __repr__(self) -> str:
        return f"IndicatorCalculator(cache={len(self._cache)})"


# ---------- Konvenienz-Funktion ----------

def compute_indicators(
    symbol: str,
    timeframe: str,
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    calculator: Optional[IndicatorCalculator] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Kurzform für einmalige Berechnung außerhalb des laufenden Systems."""
    calc = calculator or IndicatorCalculator()
    vals = calc.compute(symbol, timeframe, opens, highs, lows, closes, volumes, params)
    return vals.to_dict() if vals else None
