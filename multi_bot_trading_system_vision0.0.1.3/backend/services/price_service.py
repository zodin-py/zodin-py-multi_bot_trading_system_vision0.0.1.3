"""Price service — Binance WebSocket live ticker feed."""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import websocket

logger = logging.getLogger(__name__)


class PriceService:
    """Fetches live prices via Binance WebSocket streams.

    Subscribes to !miniTicker@arr (all markets) on startup.
    Prices are cached in memory and served instantly from REST endpoints.
    """

    # Singleton instance for WebSocket management
    _instance: Optional["PriceService"] = None
    _ws: Optional[websocket.WebSocketApp] = None
    _thread: Optional[threading.Thread] = None
    _running: bool = False

    # Cache
    _prices: Dict[str, Dict[str, Any]] = {}
    _last_update: float = 0.0
    _lock = threading.Lock()

    # WebSocket URL — !miniTicker@arr gives ALL markets in one stream
    WS_URL = "wss://stream.binance.com:9443/stream?streams=!miniTicker@arr"

    @classmethod
    def start(cls) -> None:
        """Start the WebSocket price stream in a background thread."""
        if cls._running:
            return
        cls._running = True
        thread = threading.Thread(target=cls._ws_loop, daemon=True)
        thread.start()
        logger.info("Price WebSocket stream started")

    @classmethod
    def stop(cls) -> None:
        """Stop the WebSocket stream."""
        cls._running = False
        if cls._ws:
            cls._ws.close()
        logger.info("Price WebSocket stream stopped")

    @classmethod
    def _ws_loop(cls) -> None:
        """Run the WebSocket connection loop."""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                # Handle !miniTicker@arr format: {"stream": "...", "data": [{...}, {...}]}
                if isinstance(data, dict) and "data" in data:
                    items = data["data"]
                    if not isinstance(items, list):
                        return
                    for item in items:
                        if isinstance(item, dict) and item.get("s"):
                            # Update price directly without nested lock
                            symbol = item["s"].upper()
                            if symbol.endswith("USDT"):
                                price_str = item.get("c", "0")
                                try:
                                    price = float(price_str)
                                except (ValueError, TypeError):
                                    continue
                                formatted_symbol = symbol.replace("USDT", "/USDT")
                                ts = datetime.now(tz=timezone.utc)
                                with cls._lock:
                                    cls._prices[formatted_symbol] = {
                                        "symbol": formatted_symbol,
                                        "price": price,
                                        "timestamp": ts.isoformat(),
                                    }
                                    cls._last_update = time.time()
                # Handle direct array format: [{...}, {...}]
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("s"):
                            symbol = item["s"].upper()
                            if symbol.endswith("USDT"):
                                price_str = item.get("c", "0")
                                try:
                                    price = float(price_str)
                                except (ValueError, TypeError):
                                    continue
                                formatted_symbol = symbol.replace("USDT", "/USDT")
                                ts = datetime.now(tz=timezone.utc)
                                with cls._lock:
                                    cls._prices[formatted_symbol] = {
                                        "symbol": formatted_symbol,
                                        "price": price,
                                        "timestamp": ts.isoformat(),
                                    }
                                    cls._last_update = time.time()
            except Exception as e:
                logger.warning(f"WebSocket message parse error: {e}")

        def on_error(ws, error):
            logger.warning(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket closed")
            if cls._running:
                time.sleep(1)
                cls._ws_loop()  # Reconnect

        def on_open(ws):
            logger.info("WebSocket connected")

        while cls._running:
            try:
                cls._ws = websocket.WebSocketApp(
                    cls.WS_URL,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                )
                cls._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                logger.warning(f"WebSocket connection error: {e}")
                if cls._running:
                    time.sleep(2)

    @classmethod
    def _update_price(cls, data: dict) -> None:
        """Update cached price from WebSocket data."""
        symbol = data.get("s", "").upper()
        if not symbol.endswith("USDT"):
            return
        price_str = data.get("c", "0")
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            return
        ts = datetime.now(tz=timezone.utc)
        # Store in BTC/USDT format (with slash) to match normalization
        formatted_symbol = symbol.replace("USDT", "/USDT")
        with cls._lock:
            cls._prices[formatted_symbol] = {
                "symbol": formatted_symbol,
                "price": price,
                "timestamp": ts.isoformat(),
            }
            cls._last_update = time.time()

    @classmethod
    def get_cached_prices(cls) -> Dict[str, Dict[str, Any]]:
        """Return all cached prices."""
        with cls._lock:
            return dict(cls._prices)

    @classmethod
    def get_price_sync(cls, coin: str) -> Dict[str, Any]:
        """Get price from cache (instant, no network call).

        Falls back to REST if cache is empty or stale (> 60s).
        """
        symbol = cls._normalize_symbol(coin)
        with cls._lock:
            cached = cls._prices.get(symbol)

        if cached and time.time() - cls._last_update < 60:
            return cached

        # Fallback to REST if no valid cache
        logger.info(f"Cache miss/stale for {symbol}, using REST fallback")
        return cls._fetch_price_rest(symbol)

    @staticmethod
    def _normalize_symbol(coin: str) -> str:
        """Normalize coin symbol to BTC/USDT format (always with slash)."""
        symbol = coin.strip().upper()
        # Already has slash format
        if symbol.endswith("/USDT"):
            return symbol
        # No USDT suffix - add it and then add slash
        if not symbol.endswith("USDT"):
            symbol = symbol + "USDT"
        # Convert BTCUSDT to BTC/USDT
        return symbol[:-4] + "/USDT"

    @classmethod
    def _fetch_price_rest(cls, symbol: str) -> Dict[str, Any]:
        """REST fallback for price fetch using spot market."""
        import ccxt
        try:
            # ccxt expects symbol without slash (BTCUSDT not BTC/USDT)
            exchange_symbol = symbol.replace("/", "")
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'timeout': 15000,
                'options': {'defaultType': 'spot'},
            })
            ticker = exchange.fetch_ticker(exchange_symbol)
            # Return with slash format for consistency
            return {
                'symbol': symbol,
                'price': ticker.get('last', 0.0),
                'timestamp': datetime.fromtimestamp(
                    ticker.get('timestamp', 0) / 1000, tz=timezone.utc
                ).isoformat(),
            }
        except Exception as e:
            logger.warning(f"REST fallback failed for {symbol}: {e}")
            return {'error': 'Coin not found', 'data': None}
