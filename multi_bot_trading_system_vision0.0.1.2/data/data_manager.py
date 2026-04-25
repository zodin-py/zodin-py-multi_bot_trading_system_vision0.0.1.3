# filepath: data/data_manager.py
"""
Data Manager - Binance WebSocket & OHLCV Daten
Verwaltet Echtzeit-Marktdaten von Binance
"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

import requests
import websockets
from config import BASE_URL, COINS, TIMEFRAMES


logger = logging.getLogger(__name__)


class DataManager:
    """Verwaltet Marktdaten von Binance WebSocket und REST API"""
    
    def __init__(self):
        self.candles: Dict[str, Dict[str, deque]] = {}
        self.current_prices: Dict[str, float] = {}
        self.ws_connection = None
        self.ws_thread = None
        self.running = False
        self.subscriptions = set()
        
        for coin in COINS:
            self.candles[coin] = {}
            for tf in TIMEFRAMES.keys():
                self.candles[coin][tf] = deque(maxlen=500)
    
    def get_historical_klines(self, symbol: str, timeframe: str, limit: int = 500) -> List[dict]:
        """Hole historische Klines von Binance REST API"""
        try:
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m',
                '1h': '1h', '4h': '4h', '1d': '1d'
            }
            interval = interval_map.get(timeframe, '5m')
            
            url = f"{BASE_URL}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            
            candles = []
            for k in klines:
                candles.append({
                    'time': int(k[0]),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5]),
                    'close_time': int(k[6]),
                    'quote_volume': float(k[7]),
                    'trades': int(k[8])
                })
            
            return candles
            
        except Exception as e:
            logger.error(f"Error fetching historical klines for {symbol}: {e}")
            return []
    
    def load_historical_data(self, symbol: str, timeframe: str) -> bool:
        """Lade historische Daten beim Start"""
        try:
            klines = self.get_historical_klines(symbol, timeframe)
            if klines:
                self.candles[symbol][timeframe] = deque(klines, maxlen=500)
                if klines:
                    self.current_prices[symbol] = klines[-1]['close']
                logger.info(f"Loaded {len(klines)} candles for {symbol} {timeframe}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading historical data for {symbol} {timeframe}: {e}")
            return False
    
    async def websocket_handler(self):
        """WebSocket Handler für Echtzeit-Daten"""
        from config import WS_URL
        
        while self.running:
            try:
                async with websockets.connect(WS_URL) as ws:
                    self.ws_connection = ws
                    logger.info("WebSocket connected")
                    
                    if self.subscriptions:
                        streams = [f"{s.lower()}@kline_1m" for s in self.subscriptions]
                        subscribe_msg = {
                            'method': 'SUBSCRIBE',
                            'params': streams,
                            'id': 1
                        }
                        await ws.send(json.dumps(subscribe_msg))
                    
                    while self.running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=30)
                            self._process_websocket_message(json.loads(message))
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"WebSocket error: {e}")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(5)
    
    def _process_websocket_message(self, message: dict):
        """Verarbeite WebSocket Nachricht"""
        try:
            if 'k' in message:
                kline = message['k']
                symbol = kline['s']
                timeframe = kline['i']
                
                candle = {
                    'time': kline['t'],
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v']),
                    'closed': kline['x']
                }
                
                self.current_prices[symbol] = candle['close']
                
                tf = self._normalize_timeframe(timeframe)
                if tf and symbol in self.candles:
                    if tf in self.candles[symbol]:
                        existing = self.candles[symbol][tf]
                        if existing and existing[-1]['time'] == candle['time']:
                            existing[-1] = candle
                        else:
                            existing.append(candle)
                            
        except Exception as e:
            logger.debug(f"Error processing websocket message: {e}")
    
    def _normalize_timeframe(self, tf: str) -> Optional[str]:
        """Normalisiere Timeframe zu unserem Format"""
        mapping = {
            '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m',
            '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h',
            '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d',
            '1M': '1M'
        }
        return mapping.get(tf)
    
    def subscribe(self, symbol: str):
        """Subscribe zu einem Coin"""
        self.subscriptions.add(symbol)
    
    def unsubscribe(self, symbol: str):
        """Unsubscribe von einem Coin"""
        self.subscriptions.discard(symbol)
    
    def start(self):
        """Starte WebSocket-Verbindung"""
        if not self.running:
            self.running = True
            self.ws_thread = threading.Thread(target=self._run_async_loop, daemon=True)
            self.ws_thread.start()
            logger.info("DataManager started")
    
    def stop(self):
        """Stoppe WebSocket-Verbindung"""
        self.running = False
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
        logger.info("DataManager stopped")
    
    def _run_async_loop(self):
        """Führe async WebSocket in separatem Thread aus"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.websocket_handler())
        finally:
            loop.close()
    
    def get_candles(self, symbol: str, timeframe: str) -> List[dict]:
        """Hole Candles für einen Coin und Timeframe"""
        if symbol in self.candles and timeframe in self.candles[symbol]:
            return list(self.candles[symbol][timeframe])
        return []
    
    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[dict]:
        """Hole das neueste Candle"""
        candles = self.get_candles(symbol, timeframe)
        return candles[-1] if candles else None
    
    def get_current_price(self, symbol: str) -> float:
        """Hole aktuellen Preis"""
        return self.current_prices.get(symbol, 0.0)
    
    def get_ohlcv(self, symbol: str, timeframe: str, periods: int = 14) -> tuple:
        """Hole OHLCV Daten für Indikatoren"""
        candles = self.get_candles(symbol, timeframe)
        
        if len(candles) < periods:
            return None
        
        opens = [c['open'] for c in candles[-periods:]]
        highs = [c['high'] for c in candles[-periods:]]
        lows = [c['low'] for c in candles[-periods:]]
        closes = [c['close'] for c in candles[-periods:]]
        volumes = [c['volume'] for c in candles[-periods:]]
        
        return opens, highs, lows, closes, volumes


_data_manager = None

def get_data_manager() -> DataManager:
    """Hole die DataManager Singleton Instanz"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager