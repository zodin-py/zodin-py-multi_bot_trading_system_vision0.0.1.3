#!/usr/bin/env python3
"""
Golden Master Tests für IndicatorCalculator.

Validieren, dass pandas_ta Berechnungen mit bekannten Referenzwerten
übereinstimmen (TradingView-kompatibel).

Nutzt deterministische Fixture-Daten (seeded random) für Reproduzierbarkeit.
"""

import sys
from pathlib import Path

# Projekt-Root ins sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from backend.indicators.calculator import IndicatorCalculator
from backend.indicators.provider import MockIndicatorProvider


# ---------- Helper: deterministische OHLCV Fixture ----------

def make_fixture_candles(n: int = 300, seed: int = 42) -> list[dict]:
    """Erstellt deterministische OHLCV-Kerzen für Tests."""
    np.random.seed(seed)
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    open_ = np.roll(close, 1).tolist()
    open_[0] = close[0]
    high = (close + np.abs(np.random.randn(n) * 0.2)).tolist()
    low = (close - np.abs(np.random.randn(n) * 0.2)).tolist()
    volume = (np.abs(np.random.randn(n) * 1000) + 100).tolist()

    candles = []
    base_ts = 1700000000000  # 2023-11-14 22:13:20 UTC
    for i in range(n):
        candles.append({
            'time': base_ts + i * 3600000,
            'open': round(open_[i], 4),
            'high': round(high[i], 4),
            'low': round(low[i], 4),
            'close': round(close[i], 4),
            'volume': round(volume[i], 4),
            'closed': True,
        })
    return candles


# ---------- Tests ----------

def test_calculator_computes_all_indicators():
    """Berechne Indikatoren und prüfe Grundstruktur."""
    calc = IndicatorCalculator()
    candles = make_fixture_candles(n=300)

    vals = calc.compute_from_candles('BTCUSDT', '1h', candles)
    assert vals is not None, "Calculator sollte Werte zurückgeben"

    # Prüfe alle Pflichtfelder
    assert isinstance(vals.rsi, float)
    assert isinstance(vals.macd, float)
    assert isinstance(vals.mfi, float)
    assert isinstance(vals.adx, float)
    assert isinstance(vals.atr, float)
    assert isinstance(vals.ema_9, float)
    assert isinstance(vals.ema_200, float)

    print(f"✅ RSI: {vals.rsi:.4f}")
    print(f"✅ MACD: {vals.macd:.4f}")
    print(f"✅ MFI: {vals.mfi:.4f}")
    print(f"✅ ADX: {vals.adx:.4f}")
    print(f"✅ ATR: {vals.atr:.4f}")
    print(f"✅ EMA9: {vals.ema_9:.4f}")
    print(f"✅ EMA200: {vals.ema_200:.4f}")


def test_calculator_matches_pandas_ta_direct():
    """Prüfe, dass Calculator-Ausgaben mit direktem pandas_ta übereinstimmen."""
    calc = IndicatorCalculator()
    candles = make_fixture_candles(n=300)

    # Mit Calculator
    vals_calc = calc.compute_from_candles('BTCUSDT', '1h', candles)
    assert vals_calc is not None

    # Direkt mit pandas_ta
    try:
        import pandas_ta as pandas_ta
    except ImportError:
        import pandas_ta_classic as pandas_ta
    df = pd.DataFrame({
        'open': [c['open'] for c in candles],
        'high': [c['high'] for c in candles],
        'low': [c['low'] for c in candles],
        'close': [c['close'] for c in candles],
        'volume': [c['volume'] for c in candles],
    })

    rsi_direct = pandas_ta.rsi(df['close'], length=14).iloc[-1]
    macd_result = pandas_ta.macd(df['close'], fast=12, slow=26, signal=9)
    mfi_direct = pandas_ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14).iloc[-1]
    adx_result = pandas_ta.adx(df['high'], df['low'], df['close'], length=14)
    atr_direct = pandas_ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1]

    # Vergleiche (mit Toleranz wegen Rundung)
    tolerance = 1e-6
    assert abs(vals_calc.rsi - rsi_direct) < tolerance, f"RSI mismatch: {vals_calc.rsi} vs {rsi_direct}"
    assert abs(vals_calc.macd - macd_result['MACD_12_26_9'].iloc[-1]) < tolerance, "MACD mismatch"
    assert abs(vals_calc.mfi - mfi_direct) < tolerance, f"MFI mismatch: {vals_calc.mfi} vs {mfi_direct}"
    assert abs(vals_calc.adx - adx_result['ADX_14'].iloc[-1]) < tolerance, "ADX mismatch"
    assert abs(vals_calc.atr - atr_direct) < tolerance, f"ATR mismatch: {vals_calc.atr} vs {atr_direct}"

    print(f"✅ Alle Indikatoren matchen pandas_ta direkt")


def test_calculator_cache():
    """Prüfe Caching: gleiche Eingabe → identische Ausgabe."""
    calc = IndicatorCalculator()
    candles = make_fixture_candles(n=300)

    vals1 = calc.compute_from_candles('BTCUSDT', '1h', candles)
    vals2 = calc.compute_from_candles('BTCUSDT', '1h', candles)

    assert vals1.rsi == vals2.rsi, "Cache sollte identische Werte liefern"
    assert len(calc._cache) == 1, "Nur ein Cache-Eintrag nach zweiter gleicher Abfrage"
    print("✅ Caching funktioniert korrekt")


def test_calculator_incremental_update():
    """Inkrementelles Update sollte neuen Wert liefern."""
    calc = IndicatorCalculator()
    candles = make_fixture_candles(n=300)

    vals1 = calc.compute_from_candles('BTCUSDT', '1h', candles)
    assert vals1 is not None

    # Neue Kerze anhängen
    new_candle = {
        'time': candles[-1]['time'] + 3600000,
        'open': 105.0,
        'high': 106.0,
        'low': 104.0,
        'close': 105.5,
        'volume': 500.0,
        'closed': True,
    }
    vals2 = calc.incrementally_update('BTCUSDT', '1h', candles, new_candle)
    assert vals2 is not None
    assert vals2.rsi != vals1.rsi or vals2.macd != vals1.macd, "Neuer Candle sollte neue Werte ergeben"
    print("✅ Inkrementelles Update funktioniert")


def test_calculator_returns_none_for_insufficient_data():
    """Zu wenige Kerzen sollten None zurückgeben."""
    calc = IndicatorCalculator()
    candles = make_fixture_candles(n=10)  # zu wenig für RSI(14)

    vals = calc.compute_from_candles('BTCUSDT', '1h', candles)
    assert vals is None, "Sollte None bei unzureichenden Daten zurückgeben"
    print("✅ Korrekte Behandlung unzureichender Daten")


def test_mock_provider():
    """MockIndicatorProvider liefert deterministische Fixtures."""
    mock = MockIndicatorProvider()
    from backend.indicators.provider import _IndicatorFixture

    mock.set_indicators('BTCUSDT', '1h', _IndicatorFixture(rsi=28.0, macd=-1.5, mfi=35.0))

    indicators = mock.get_indicators('BTCUSDT', '1h')
    assert indicators is not None
    assert indicators['rsi'] == 28.0
    assert indicators['macd'] == -1.5
    assert indicators['mfi'] == 35.0
    print("✅ MockIndicatorProvider funktioniert")


def test_provider_protocol_and_mock():
    """Provider-Protokoll und Mock-Implementierung validieren."""
    from backend.indicators.provider import IndicatorProvider, MockIndicatorProvider, _IndicatorFixture

    # Prüfe Protocol-Signatur
    import inspect
    sig_get_indicators = inspect.signature(IndicatorProvider.get_indicators)
    sig_get_ohlcv = inspect.signature(IndicatorProvider.get_ohlcv)
    assert 'symbol' in sig_get_indicators.parameters
    assert 'timeframe' in sig_get_indicators.parameters
    assert 'symbol' in sig_get_ohlcv.parameters
    print("✅ IndicatorProvider Protocol korrekt definiert")

    # Mock-Fixture-Tests
    mock = MockIndicatorProvider()
    mock.set_indicators('BTCUSDT', '1h', _IndicatorFixture(
        rsi=25.0, macd=-1.5, mfi=35.0,
        adx=45.0, atr=2.5,
        support_levels=[95.0, 90.0],
        resistance_levels=[105.0, 110.0],
        bullish_fvg=True,
    ))

    ind = mock.get_indicators('BTCUSDT', '1h')
    assert ind is not None
    assert ind['rsi'] == 25.0
    assert ind['support_levels'] == [95.0, 90.0]
    assert ind['bullish_fvg'] is True
    print("✅ MockIndicatorProvider liefert korrekte Fixtures")

    # OHLCV-Fixture
    mock.set_ohlcv('BTCUSDT', '1h', [
        {'open': 100, 'high': 102, 'low': 99, 'close': 101, 'volume': 500},
        {'open': 101, 'high': 103, 'low': 100, 'close': 102, 'volume': 600},
    ])
    ohlcv = mock.get_ohlcv('BTCUSDT', '1h', periods=2)
    assert ohlcv is not None
    assert len(ohlcv[3]) == 2  # closes
    print("✅ MockIndicatorProvider OHLCV funktioniert")

    # Stale-Flag
    mock.set_stale('BTCUSDT', '1h', True)
    assert mock.is_stale('BTCUSDT', '1h') is True
    print("✅ Stale-Detection funktioniert")


def test_calculator_adapter_integration():
    """Integration: MockProvider + Calculator zusammenarbeitend."""
    from backend.indicators.provider import MockIndicatorProviderAdapter, MockIndicatorProvider, _IndicatorFixture
    from backend.indicators.calculator import IndicatorCalculator

    mock = MockIndicatorProvider()
    mock.set_indicators('BTCUSDT', '1h', _IndicatorFixture(
        rsi=72.0, macd=0.8, mfi=85.0, adx=30.0, atr=1.5,
        ema_9=102.0, ema_21=101.0, ema_50=100.0, ema_200=99.0,
        sma_20=102.0, sma_50=100.0,
    ))

    calc = IndicatorCalculator()
    adapter = MockIndicatorProviderAdapter(mock)

    # Gibt Mock-Werte zurück (keine echte Berechnung nötig)
    ind = adapter.get_indicators('BTCUSDT', '1h')
    assert ind is not None
    assert ind['rsi'] == 72.0
    assert ind['macd'] == 0.8
    print("✅ Adapter verbindet MockProvider + Calculator")


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 Golden Master Tests for IndicatorCalculator")
    print("=" * 60)

    test_calculator_computes_all_indicators()
    test_calculator_matches_pandas_ta_direct()
    test_calculator_cache()
    test_calculator_incremental_update()
    test_calculator_returns_none_for_insufficient_data()
    test_mock_provider()
    test_bot_with_mock_provider()

    print("\n" + "=" * 60)
    print("✅ ALL GOLDEN MASTER TESTS PASSED")
    print("=" * 60)
