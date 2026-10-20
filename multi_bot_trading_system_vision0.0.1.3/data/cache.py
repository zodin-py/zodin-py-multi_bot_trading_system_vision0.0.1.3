# filepath: data/cache.py
"""
Market Cache - Persistenter DuckDB-Cache für Kerzen (Candles) und Indikatoren.

Ersetzt den flüchtigen deque-Cache des alten DataManager:
- überlebt Prozess-Neustarts
- nach Zeitbereich abfragbar (für Backtesting)
- TTL-basierte Bereinigung (purge_expired)

Tabellen:
- candles(symbol, timeframe, open_ts, open, high, low, close, volume, closed)
- indicators(symbol, timeframe, ts, params_hash, payload_json)
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import duckdb

from config import CACHE_TTL_SEC, DUCKDB_PATH


logger = logging.getLogger(__name__)

# Standard-Aufbewahrung für Kerzen in Tagen (älter -> purge)
DEFAULT_RETENTION_DAYS = 90


class MarketCache:
    """Persistenter Markt-Daten-Cache auf DuckDB-Basis."""

    def __init__(self, path: str = DUCKDB_PATH):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = duckdb.connect(path)
        self._init_schema()

    # ---------------- Schema ----------------

    def _init_schema(self):
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candles (
                    symbol     VARCHAR,
                    timeframe  VARCHAR,
                    open_ts    BIGINT,
                    open       DOUBLE,
                    high       DOUBLE,
                    low        DOUBLE,
                    close      DOUBLE,
                    volume     DOUBLE,
                    closed     BOOLEAN,
                    PRIMARY KEY (symbol, timeframe, open_ts)
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS indicators (
                    symbol       VARCHAR,
                    timeframe    VARCHAR,
                    ts           BIGINT,
                    params_hash  VARCHAR,
                    payload      VARCHAR,
                    PRIMARY KEY (symbol, timeframe, ts, params_hash)
                )
                """
            )

    # ---------------- Candles ----------------

    def store_candles(self, symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> int:
        """UPSERT einer Kerzen-Liste (Dicts mit time/open/high/low/close/volume/closed)."""
        if not candles:
            return 0
        rows = []
        for c in candles:
            rows.append((
                symbol,
                timeframe,
                int(c.get('time', c.get('open_ts', 0))),
                float(c['open']),
                float(c['high']),
                float(c['low']),
                float(c['close']),
                float(c['volume']),
                bool(c.get('closed', True)),
            ))
        with self._lock:
            self._conn.executemany(
                """
                INSERT OR REPLACE INTO candles
                    (symbol, timeframe, open_ts, open, high, low, close, volume, closed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start_ms: Optional[int] = None,
        end_ms: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Kerzen aufsteigend nach Zeit. limit = die letzten N Kerzen."""
        query = (
            "SELECT open_ts, open, high, low, close, volume, closed FROM candles "
            "WHERE symbol = ? AND timeframe = ?"
        )
        params = [symbol, timeframe]
        if start_ms is not None:
            query += " AND open_ts >= ?"
            params.append(int(start_ms))
        if end_ms is not None:
            query += " AND open_ts <= ?"
            params.append(int(end_ms))

        with self._lock:
            df = self._conn.execute(query, params).df()

        df = df.sort_values('open_ts')
        if limit is not None:
            df = df.tail(int(limit))

        return [
            {
                'time': int(r.open_ts),
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': r.volume,
                'closed': bool(r.closed),
            }
            for r in df.itertuples()
        ]

    def candle_count(self, symbol: str, timeframe: str) -> int:
        with self._lock:
            df = self._conn.execute(
                "SELECT COUNT(*) AS n FROM candles WHERE symbol = ? AND timeframe = ?",
                [symbol, timeframe],
            ).df()
        return int(df['n'].iloc[0]) if not df.empty else 0

    def latest_close_ts(self, symbol: str, timeframe: str) -> Optional[int]:
        """Zeitstempel (ms) der neuesten Kerze, oder None wenn leer."""
        with self._lock:
            df = self._conn.execute(
                "SELECT MAX(open_ts) AS ts FROM candles WHERE symbol = ? AND timeframe = ?",
                [symbol, timeframe],
            ).df()
        if df.empty:
            return None
        val = df['ts'].iloc[0]
        if val is None:
            return None
        # Handle NA/null from DuckDB
        if hasattr(val, '__float__') and not (val == val):  # NaN check
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def purge_expired(self, retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
        """Löscht Kerzen älter als retention_days. Gibt Anzahl gelöschter Zeilen zurück."""
        cutoff_ms = int((time.time() - retention_days * 86400) * 1000)
        with self._lock:
            before = self._conn.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
            self._conn.execute("DELETE FROM candles WHERE open_ts < ?", [cutoff_ms])
            after = self._conn.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
        deleted = before - after
        # Ebenso abgelaufene Indikator-Snapshots
        with self._lock:
            self._conn.execute(
                "DELETE FROM indicators WHERE ts < ?",
                [int(time.time() * 1000) - CACHE_TTL_SEC * 1000],
            )
        return deleted

    # ---------------- Indicators ----------------

    def store_indicators(
        self,
        symbol: str,
        timeframe: str,
        params_hash: str,
        values: Dict[str, Any],
        ts_ms: Optional[int] = None,
    ):
        """Speichere berechnete Indikatorwerte als JSON-Snapshot."""
        ts = int(ts_ms if ts_ms is not None else time.time() * 1000)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO indicators
                    (symbol, timeframe, ts, params_hash, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                [symbol, timeframe, ts, params_hash, json.dumps(values)],
            )

    def get_indicators(
        self,
        symbol: str,
        timeframe: str,
        params_hash: str,
        max_age_sec: int = CACHE_TTL_SEC,
    ) -> Optional[Dict[str, Any]]:
        """Neuester_snapshot, sofern nicht älter als max_age_sec, sonst None."""
        cutoff = int(time.time() * 1000) - max_age_sec * 1000
        with self._lock:
            df = self._conn.execute(
                """
                SELECT ts, payload FROM indicators
                WHERE symbol = ? AND timeframe = ? AND params_hash = ? AND ts >= ?
                ORDER BY ts DESC LIMIT 1
                """,
                [symbol, timeframe, params_hash, cutoff],
            ).df()
        if df.empty:
            return None
        return json.loads(df['payload'].iloc[0])

    # ---------------- Lifecycle ----------------

    def close(self):
        with self._lock:
            self._conn.close()

    def __repr__(self) -> str:
        return f"MarketCache(path={self.path!r})"
