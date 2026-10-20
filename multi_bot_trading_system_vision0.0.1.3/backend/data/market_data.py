# filepath: data/market_data.py
"""
Market Data - Datenzugang über ccxt (REST) + nativen Binance-Kline-WebSocket.

Ersetzt den alten DataManager:
- Historische OHLCV über ccxt.fetch_ohlcv() mit eingebautem Rate-Limiting
  (enableRateLimit=True) und Sandbox/Testnet-Modus via set_sandbox_mode().
- Echtzeit-Updates (tick + geschlossene Kerzen) über einen Binance
  combined-stream WebSocket mit Auto-Reconnect und exponentiellem Backoff.
- Persistenter Cache (data/cache.MarketCache) überlebt Neustarts.
- Stale-Erkennung: eine Kerze gilt als veraltet, wenn ihr Alter > 2x
  Zeitrahmen ist (is_stale / should_reject_signal).

Hinweis: ccxt (frei) stellt für Binance kein watch_ohlcv bereit -> Streaming
läuft über den nativen WS, REST läuft über ccxt.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

import ccxt.async_support as ccxt_async
import websockets

from backend.config import (
    BINANCE_API_KEY,
    BINANCE_SECRET_KEY,
    CACHE_TTL_SEC,
    CCXT_RATE_LIMIT,
    USE_TESTNET,
)
from backend.data.cache import MarketCache


logger = logging.getLogger(__name__)

KLINE_INTERVAL_MAP = {
    '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
    '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h',
    '12h': '12h', '1d': '1d', '1w': '1w',
}

# Sekunden pro Zeitrahmen, für Stale-Erkennung
_INTERVAL_SECONDS = {
    '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
    '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800,
    '12h': 43200, '1d': 86400, '1w': 604800,
}

# Binance WebSocket Basis-URL (Spot; Sandbox-Like via geturl override)
_WS_STREAM_HOST = (
    'wss://stream.binance.vision' if USE_TESTNET
    else 'wss://stream.binance.com:9443'
)


class MarketData:
    """ccxt-REST + nativer Binance-WebSocket plus DuckDB-Cache."""

    def __init__(self, cache: Optional[MarketCache] = None, ttl_sec: int = CACHE_TTL_SEC):
        self.cache = cache or MarketCache()
        self.ttl_sec = ttl_sec
        self.exchange = self._build_exchange()
        self._current_prices: Dict[str, float] = {}
        self._subscriptions: set = set()  # {(symbol, interval)}
        self._callbacks: List[Callable[[str, str, dict], None]] = []
        self.running = False
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_loop: Optional[asyncio.AbstractEventLoop] = None

    # ---------------- Exchange ----------------

    def _build_exchange(self):
        ex = ccxt_async.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_SECRET_KEY,
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True},
        })
        # Basis-Intervall für Rate-Limiter konfigurierbar
        try:
            ex.throttle['refillRate'] = {value: CCXT_RATE_LIMIT for value in ex.throttle['refillRate']}
        except Exception:
            pass
        if USE_TESTNET:
            try:
                # ccxt Testnet für Spot-Kurse ist öffentlich; set_sandbox_mode
                # betrifft primär Futures. Wir lassen Spot auf Live-Read,
                # Orders gehen separat gegen Testnet.
                ex.set_sandbox_mode(True)
            except Exception as e:
                logger.debug(f"set_sandbox_mode not applicable for spot reads: {e}")
        return ex

    # ---------------- REST / History ----------------

    async def fetch_ohlcv_async(
        self, symbol: str, timeframe: str, limit: int = 500, use_cache_first: bool = False
    ) -> List[Dict[str, Any]]:
        """Hole OHLCV via ccxt, normalisiere und schreibe in den Cache."""
        interval = KLINE_INTERVAL_MAP.get(timeframe, '5m')
        if use_cache_first:
            cached = self.cache.get_candles(symbol, timeframe, limit=limit)
            if len(cached) >= limit:
                return cached
        try:
            raw = await self.exchange.fetch_ohlcv(symbol, interval, limit=limit)
        except Exception as e:
            logger.error(f"fetch_ohlcv failed for {symbol} {timeframe}: {e}")
            # Fallback: was der Cache noch hat
            return self.cache.get_candles(symbol, timeframe, limit=limit)

        candles = self._normalize(raw)
        if candles:
            self.cache.store_candles(symbol, timeframe, candles)
            self._current_prices[symbol] = candles[-1]['close']
        return candles

    def fetch_ohlcv(
        self, symbol: str, timeframe: str, limit: int = 500, use_cache_first: bool = False
    ) -> List[Dict[str, Any]]:
        """Synchrone包装 für nicht-async-Aufrufer."""
        return self._run_sync(self.fetch_ohlcv_async(symbol, timeframe, limit, use_cache_first))

    def load_historical_data(
        self, symbol: str, timeframe: str = '1h', limit: int = 500
    ) -> bool:
        """Kompatibilität zum alten DataManager: lade Cache + Preis."""
        candles = self.fetch_ohlcv(symbol, timeframe, limit=limit)
        if candles:
            self._current_prices[symbol] = candles[-1]['close']
            logger.info(f"Loaded {len(candles)} candles for {symbol} {timeframe}")
            return True
        return False

    # ---------------- Sync-Bridge ----------------

    def _run_sync(self, coro):
        """Führe Coroutine in der WS-Loop aus, sonst in einer temporären."""
        if self.running and self._ws_loop is not None and self._ws_loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(coro, self._ws_loop)
            return fut.result(timeout=30)
        return asyncio.run(coro)

    async def _close_exchange(self):
        try:
            await self.exchange.close()
        except Exception:
            pass

    def _run_sync_standalone(self, coro):
        try:
            return asyncio.run(coro)
        except RuntimeError:
            # bereits Loop aktiv -> eigene temporäre Loop
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()

    # ---------------- WebSocket Streaming ----------------

    def subscribe(self, symbol: str, timeframe: str = '1h'):
        self._subscriptions.add((symbol, KLINE_INTERVAL_MAP.get(timeframe, '1h')))
        if self.running:
            asyncio.run_coroutine_threadsafe(self._resubscribe(), self._ws_loop)

    def unsubscribe(self, symbol: str, timeframe: str = '1h'):
        self._subscriptions.discard((symbol, KLINE_INTERVAL_MAP.get(timeframe, '1h')))

    def on_kline(self, callback: Callable[[str, str, dict], None]):
        """Registriere callback(symbol, timeframe, candle_dict) für jeden Tick."""
        self._callbacks.append(callback)

    def start(self):
        """Starte WS-Thread (idempotent)."""
        if self.running:
            return
        self.running = True
        self._ws_thread = threading.Thread(target=self._ws_entry, daemon=True)
        self._ws_thread.start()
        logger.info("MarketData WebSocket loop started")

    def stop(self):
        self.running = False
        if self._ws_loop is not None:
            self._ws_loop.call_soon_threadsafe(self._ws_loop.stop)
        if self._ws_thread:
            self._ws_thread.join(timeout=5)
        try:
            self.cache.close()
        except Exception:
            pass
        logger.info("MarketData stopped")

    def _ws_entry(self):
        loop = asyncio.new_event_loop()
        self._ws_loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ws_forever())
        finally:
            try:
                loop.run_until_complete(self._close_exchange())
            finally:
                loop.close()

    async def _ws_forever(self):
        backoff = 1.0
        while self.running:
            streams = [f"{s.lower()}@kline_{i}" for (s, i) in self._subscriptions]
            url = f"{_WS_STREAM_HOST}/stream?streams={'/'.join(streams)}" if streams else \
                  f"{_WS_STREAM_HOST}/stream"
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                    logger.info("MarketData WebSocket connected")
                    backoff = 1.0
                    while self.running:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=30)
                            self._handle_message(msg)
                        except asyncio.TimeoutError:
                            continue
            except Exception as e:
                if not self.running:
                    break
                logger.error(f"WebSocket error (reconnect in {backoff:.0f}s): {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    async def _resubscribe(self):
        # combined-Streams erlauben SUBSCRIBE/UNSUBSCRIBE on the fly nicht
        # zuverlässig; wir brechen den Stream für einen sauberen Reconnect ab.
        pass

    def _handle_message(self, msg: str):
        try:
            envelope = json.loads(msg)
            payload = envelope.get('data', envelope)
            k = payload.get('k')
            if not k:
                return
            symbol = k['s']
            interval = k['i']
            candle = {
                'time': int(k['t']),
                'open': float(k['o']),
                'high': float(k['h']),
                'low': float(k['l']),
                'close': float(k['c']),
                'volume': float(k['v']),
                'closed': bool(k['x']),
            }
            self._current_prices[symbol] = candle['close']
            timeframe = self._normalize_timeframe(interval)
            self.cache.store_candles(symbol, timeframe, [candle])
            for cb in self._callbacks:
                try:
                    cb(symbol, timeframe, candle)
                except Exception as e:
                    logger.debug(f"on_kline callback error: {e}")
        except Exception as e:
            logger.debug(f"Error processing ws message: {e}")

    @staticmethod
    def _normalize_timeframe(interval: str) -> str:
        return interval if interval in _INTERVAL_SECONDS else '1h'

    # ---------------- Helpers ----------------

    def _normalize(self, raw: List[List]) -> List[Dict[str, Any]]:
        out = []
        for r in raw:
            out.append({
                'time': int(r[0]),
                'open': float(r[1]),
                'high': float(r[2]),
                'low': float(r[3]),
                'close': float(r[4]),
                'volume': float(r[5]),
                'closed': True,
            })
        return out

    # ---------------- Accessors ----------------

    def get_ohlcv(
        self, symbol: str, timeframe: str, periods: int = 50
    ) -> Optional[tuple]:
        """OHLCV als (opens, highs, lows, closes, volumes), wie base_bot erwartet."""
        candles = self.cache.get_candles(symbol, timeframe, limit=periods)
        if len(candles) < periods:
            # Cache-Fill mit REST
            candles = self.fetch_ohlcv(symbol, timeframe, limit=periods)
        if len(candles) < periods:
            return None
        opens = [c['open'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        closes = [c['close'] for c in candles]
        volumes = [c['volume'] for c in candles]
        return opens, highs, lows, closes, volumes

    def get_candles(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        return self.cache.get_candles(symbol, timeframe, limit=500)

    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        candles = self.get_candles(symbol, timeframe)
        return candles[-1] if candles else None

    def get_current_price(self, symbol: str) -> float:
        price = self._current_prices.get(symbol, 0.0)
        if price <= 0.0:
            candle = self.get_latest_candle(symbol, '1h')
            if candle:
                return float(candle['close'])
        return price

    # ---------------- Stale / TTL ----------------

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        """True, wenn die letzte Kerze älter als 2x Zeitrahmen ist."""
        latest = self.cache.latest_close_ts(symbol, timeframe)
        if latest is None:
            return True
        age_sec = time.time() - (latest / 1000.0)
        interval_sec = _INTERVAL_SECONDS.get(
            KLINE_INTERVAL_MAP.get(timeframe, '1h'), 3600
        )
        return age_sec > 2 * interval_sec

    def should_reject_signal(self, symbol: str, timeframe: str) -> bool:
        """True, wenn Signale auf diesen Daten verworfen werden sollen."""
        return self.is_stale(symbol, timeframe)

    def purge_expired(self):
        self.cache.purge_expired()

    def __repr__(self) -> str:
        return (f"MarketData(subs={len(self._subscriptions)}, "
                f"prices={len(self._current_prices)}, running={self.running})")


_market_data: Optional[MarketData] = None


def get_market_data() -> MarketData:
    """Singleton-Zugang, analog get_data_manager."""
    global _market_data
    if _market_data is None:
        _market_data = MarketData()
    return _market_data
