# filepath: indicators/provider.py
"""
Indicator Provider Protocol für alle Bots.

Schnittstelle, auf die alle Bots (RSI, MACD, MFI, SR, SMC, Harmonic, Trend)
zugreifen statt direkt auf DataManager/MobileData zu griffen. Ermöglicht:
- Dependency Injection für saubere Unit-Tests ohne Netzwerk
- Austauschen der Datenquelle (ccxt, historische CSVs, Simulationsdaten)
- Zentrale Caching-Strategie

Realisierte Implementierung: IndicatorProviderAdapter (aus MarketData + Calculator)
Test-Zweck: MockIndicatorProvider mit deterministischen Fixtures
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class IndicatorProvider(ABC):
    """Protocol: Alle Bots benötigen diese Methoden — sonst keine Netzwerkkopplung."""

    @abstractmethod
    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Berechnete Indikatorwerte für Symbol/Timeframe.

        Muss (mindestens) enthalten:
        - rsi (float)           – RSI(14)
        - macd, macd_signal, macd_hist (float) – MACD(12,26,9)
        - mfi (float)           – MFI(14)
        - adx, plus_di, minus_di (float)       – ADX(14)
        - atr (float)           – ATR(14)

        Zusätzliche Werte (optional, aber empfohlen):
        - ema_9, ema_21, ema_50, ema_200
        - sma_20, sma_50

        Returns None bei nicht ausreichenden Daten.
        """

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        periods: int = 50,
    ) -> Optional[Tuple[List[float], ...]]:
        """
        OHLCV-Tupel aus cached oder computed candles.

        Returns:
            (opens, highs, lows, closes, volumes) – Listen gleich lang (>= periods)
            None wenn nicht genug Daten verfügbar.
        """

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        """True, wenn die letzten Kerzen veraltet sind."""
        return False


# ---------------------------------------------------------------------------
# Adapter: MarketData + IndicatorCalculator → IndicatorProvider
# ---------------------------------------------------------------------------

from backend.indicators.calculator import IndicatorCalculator  # type: ignore[import-not-found]


class IndicatorProviderAdapter(IndicatorProvider):
    """
    Adapter, der MarketData (ccxt + WS + DuckDB) mit IndicatorCalculator
    verbindet und den Indikatoren-Cache verwaltet.

    Usage:
        provider = IndicatorProviderAdapter(market_data, calculator=IndicatorCalculator())
        values = provider.get_indicators("BTCUSDT", "1h")
    """

    def __init__(self, market_data, calculator: IndicatorCalculator):
        self.market_data = market_data
        self.calculator = calculator

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        # Cache prüfen
        cached = self.calculator.get_cached(symbol, timeframe)
        if cached is not None:
            return cached.to_dict()

        # OHLCV holen
        ohlcv = self.market_data.get_ohlcv(symbol, timeframe, periods=250)
        if ohlcv is None:
            return None

        opens, highs, lows, closes, volumes = ohlcv
        vals = self.calculator.compute(
            symbol, timeframe, list(opens), list(highs), list(lows),
            list(closes), list(volumes),
        )
        return vals.to_dict() if vals else None

    def get_ohlcv(self, symbol: str, timeframe: str, periods: int = 50) -> Optional[Tuple[List[float], ...]]:
        return self.market_data.get_ohlcv(symbol, timeframe, periods)

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        return self.market_data.is_stale(symbol, timeframe)


# Separate pure-mock adapter for unit tests without network
class MockIndicatorProviderAdapter(IndicatorProvider):
    """
    Adapter, der MockIndicatorProvider direkt weiterleitet —
    für Unit-Tests ohne Netzwerkzugriff und ohne echte Berechnung.
    """

    def __init__(self, mock_provider: MockIndicatorProvider):
        self._mock = mock_provider

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        return self._mock.get_indicators(symbol, timeframe)

    def get_ohlcv(self, symbol: str, timeframe: str, periods: int = 50) -> Optional[Tuple[List[float], ...]]:
        return self._mock.get_ohlcv(symbol, timeframe, periods)

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        return self._mock.is_stale(symbol, timeframe)


# ---------------------------------------------------------------------------
# Test-Fixture-Provider
# ---------------------------------------------------------------------------

@dataclass
class _IndicatorFixture:
    """Einzelne Snapshot-Zeile für deterministische Tests."""
    timestamp: float = 0.0
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    mfi: float = 50.0
    adx: float = 25.0
    plus_di: float = 30.0
    minus_di: float = 20.0
    atr: float = 0.0
    ema_9: float = 0.0
    ema_21: float = 0.0
    ema_50: float = 0.0
    ema_200: float = 0.0
    sma_20: float = 0.0
    sma_50: float = 0.0
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    buy_orderblocks: List[float] = field(default_factory=list)
    sell_orderblocks: List[float] = field(default_factory=list)
    bullish_fvg: bool = False
    bearish_fvg: bool = False


class MockIndicatorProvider(IndicatorProvider):
    """
    Deterministischer Provider für Unit-Tests ohne Netzwerkzugriff.

    Usage:
        provider = MockIndicatorProvider()
        provider.set_indicators("BTCUSDT", "1h", IndicatorFixture(rsi=28, macd=-1.5))
        bot = RSIBot(provider=provider)
        signal = bot.analyze("BTCUSDT", "1h")
    """

    def __init__(self):
        self._fixtures: Dict[str, Dict[str, _IndicatorFixture]] = {}
        self._ohlcvs: Dict[str, List[dict]] = {}
        self._stale: Dict[str, bool] = {}

    def set_indicators(self, symbol: str, timeframe: str, fixture: _IndicatorFixture):
        if symbol not in self._fixtures:
            self._fixtures[symbol] = {}
        self._fixtures[symbol][timeframe] = fixture

    def clear_indicators(self, symbol: str, timeframe: str):
        if symbol in self._fixtures and timeframe in self._fixtures[symbol]:
            del self._fixtures[symbol][timeframe]

    def set_ohlcv(self, symbol: str, timeframe: str, candles: List[Dict[str, Any]]):
        key = f"{symbol}:{timeframe}"
        self._ohlcvs[key] = candles

    def set_stale(self, symbol: str, timeframe: str, stale: bool):
        self._stale[f"{symbol}:{timeframe}"] = stale

    # ---- Protocol ----------------------------------------------------------

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        fixture = self._fixtures.get(symbol, {}).get(timeframe)
        if fixture is None:
            return None
        return {
            'rsi': fixture.rsi,
            'macd': fixture.macd,
            'macd_signal': fixture.macd_signal,
            'macd_hist': fixture.macd_hist,
            'mfi': fixture.mfi,
            'adx': fixture.adx,
            'plus_di': fixture.plus_di,
            'minus_di': fixture.minus_di,
            'atr': fixture.atr,
            'ema_9': fixture.ema_9,
            'ema_21': fixture.ema_21,
            'ema_50': fixture.ema_50,
            'ema_200': fixture.ema_200,
            'sma_20': fixture.sma_20,
            'sma_50': fixture.sma_50,
            'support_levels': list(fixture.support_levels),
            'resistance_levels': list(fixture.resistance_levels),
            'buy_orderblocks': list(fixture.buy_orderblocks),
            'sell_orderblocks': list(fixture.sell_orderblocks),
            'bullish_fvg': fixture.bullish_fvg,
            'bearish_fvg': fixture.bearish_fvg,
        }

    def get_ohlcv(self, symbol: str, timeframe: str, periods: int = 50) -> Optional[Tuple[List[float], ...]]:
        candles = self._ohlcvs.get(f"{symbol}:{timeframe}")
        if candles is None or len(candles) < periods:
            return None
        candles = candles[-periods:]
        return (
            [c['open'] for c in candles],
            [c['high'] for c in candles],
            [c['low'] for c in candles],
            [c['close'] for c in candles],
            [c['volume'] for c in candles],
        )

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        return self._stale.get(f"{symbol}:{timeframe}", False)
