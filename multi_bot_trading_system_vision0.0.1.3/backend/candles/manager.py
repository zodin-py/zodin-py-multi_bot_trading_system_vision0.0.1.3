#!/usr/bin/env python3
"""Candle Manager - Manages the complete lifecycle of candle data.

Responsibility: Manage candle data fetching, validation, storage, deduplication,
merge, sort, trim, load, and save operations.

Keep UI-specific code out of this module. The chart component receives validated
data through a clear interface.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSON Storage Schema
# ---------------------------------------------------------------------------

CANDLE_JSON_SCHEMA_VERSION = 1


def get_candle_data_dir() -> Path:
    """Return the directory where candle JSON files are stored."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "candles"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_candle_file_path(symbol: str, timeframe: str) -> Path:
    """Return the JSON file path for a symbol/timeframe combination."""
    candle_data_dir = get_candle_data_dir()
    return candle_data_dir / f"{symbol}_{timeframe}.json"


# ---------------------------------------------------------------------------
# Core Operations
# ---------------------------------------------------------------------------

def load_candles(symbol: str, timeframe: str) -> Tuple[Dict[str, Any], bool]:
    """Load candle data from JSON file.

    Returns:
        (candle_data, success) tuple where success is False if file not found/invalid.
    """
    file_path = get_candle_file_path(symbol, timeframe)

    if not file_path.exists():
        logger.info(f"No candle data file found at {file_path}")
        return _empty_candle_data(), False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate minimal structure
        if not isinstance(data, dict):
            logger.error(f"Invalid candle data format in {file_path}: not a dict")
            return _empty_candle_data(), False

        metadata = data.get("metadata", {})
        candles = data.get("candles", [])

        # Ensure required metadata fields exist
        if "symbol" not in metadata:
            metadata["symbol"] = symbol
        if "timeframe" not in metadata:
            metadata["timeframe"] = timeframe
        if "candle_count" not in metadata:
            metadata["candle_count"] = len(candles)
        if "version" not in metadata:
            metadata["version"] = CANDLE_JSON_SCHEMA_VERSION

        # Update metadata with current values
        metadata.setdefault("symbol", symbol)
        metadata.setdefault("timeframe", timeframe)
        metadata.setdefault("candle_count", len(candles))
        metadata.setdefault("version", CANDLE_JSON_SCHEMA_VERSION)
        metadata["last_update"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Loaded {len(candles)} candles from {file_path}")
        return data, True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return _empty_candle_data(), False
    except Exception as e:
        logger.error(f"Error loading candles from {file_path}: {e}")
        return _empty_candle_data(), False


def _empty_candle_data() -> Dict[str, Any]:
    """Return an empty candle data structure with proper metadata."""
    return {
        "metadata": {
            "exchange": "binance",
            "market_type": "spot",
            "symbol": "",
            "timeframe": "",
            "candle_count": 0,
            "last_update": "",
            "last_candle_open_time": None,
            "version": CANDLE_JSON_SCHEMA_VERSION,
        },
        "candles": [],
    }


def save_candles(symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> bool:
    """Save candle data to JSON file atomically.

    Uses atomic write procedure:
    1. Build complete updated JSON object
    2. Write to temporary file
    3. Flush and close temporary file
    4. Replace original file atomically
    5. Preserve previous valid file if operation fails
    """
    file_path = get_candle_file_path(symbol, timeframe)
    candle_data_dir = file_path.parent

    # Load existing data
    existing_data, _ = load_candles(symbol, timeframe)

    # Merge and process new candles
    merged = merge_candles(existing_data.get("candles", []), candles)

    # Trim to max 1000 candles
    merged = merged[-1000:] if len(merged) > 1000 else merged

    # Build new data object
    new_data = {
        "metadata": {
            "exchange": "binance",
            "market_type": "spot",
            "symbol": symbol,
            "timeframe": timeframe,
            "candle_count": len(merged),
            "last_update": datetime.now(timezone.utc).isoformat(),
            "last_candle_open_time": merged[-1]["open_time"] if merged else None,
            "version": CANDLE_JSON_SCHEMA_VERSION,
        },
        "candles": merged,
    }

    # Atomic write
    try:
        # Write to temporary file first
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        # Atomically replace original file
        os.replace(tmp_path, file_path)

        logger.info(f"Saved {len(merged)} candles to {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving candles to {file_path}: {e}")
        # Clean up temp file if it exists
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        return False


def merge_candles(
    existing: List[Dict[str, Any]],
    new_candles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Merge new candles with existing data, removing duplicates.

    Strategy:
    1. Combine existing + new candles
    2. Deduplicate based on unique identity (symbol + timeframe + open_time)
    3. Sort chronologically (oldest first)
    4. Trim to max 1000 candles (newest preserved)

    Args:
        existing: List of existing candle dicts from JSON
        new_candles: List of new candle dicts to merge

    Returns:
        Merged, deduplicated, sorted candle list (max 1000 entries)
    """
    if not existing:
        # No existing data, just validate and return new candles
        return _validate_candles(new_candles)

    if not new_candles:
        # No new candles, return existing (validated)
        return _validate_candles(existing)

    # Build a set of existing open_times for deduplication
    existing_times: set[int] = set()
    for candle in existing:
        ot = candle.get("open_time")
        if ot is not None:
            existing_times.add(ot)

    # Filter out duplicates from new candles
    filtered_new = []
    for candle in new_candles:
        ot = candle.get("open_time")
        if ot is None:
            logger.warning(f"Skipping candle with missing open_time: {candle}")
            continue
        if ot not in existing_times:
            filtered_new.append(candle)
        else:
            logger.debug(f"Duplicate candle detected (open_time={ot}), skipping")

    # Combine existing with filtered new candles
    combined = existing + filtered_new

    # Sort chronologically by open_time (oldest first)
    combined.sort(key=lambda c: c.get("open_time", 0))

    # Trim to max 1000 candles, preserving the newest
    if len(combined) > 1000:
        combined = combined[-1000:]
        logger.info(f"Trimmed candle data to 1000 newest candles")

    # Final validation
    result = _validate_candles(combined)
    logger.info(f"Merged {len(existing)} existing with {len(filtered_new)} new candles, "
                f"result: {len(result)} candles")

    return result


def _validate_candles(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate candle data integrity.

    Reject candles with:
    - Missing timestamps
    - Invalid numeric values
    - Negative prices
    - Negative volumes
    - High prices below low prices
    - Open or close outside the high/low range
    - Invalid timestamps
    - Incomplete status
    """
    validated: List[Dict[str, Any]] = []

    for i, candle in enumerate(candles):
        try:
            # Check required fields exist
            required_fields = ["open_time", "close_time", "open", "high", "low", "close", "volume"]
            missing = [f for f in required_fields if f not in candle or candle[f] is None]
            if missing:
                logger.warning(f"Candle {i} missing required fields {missing}, skipping")
                continue

            # Check timestamps are valid integers
            open_time = candle["open_time"]
            close_time = candle["close_time"]
            if not isinstance(open_time, (int, float)) or not isinstance(close_time, (int, float)):
                logger.warning(f"Candle {i} has invalid timestamp types, skipping")
                continue

            # Check for negative prices/volumes
            if candle["open"] < 0 or candle["high"] < 0 or candle["low"] < 0 or candle["close"] < 0:
                logger.warning(f"Candle {i} has negative price values, skipping")
                continue

            if candle["volume"] < 0:
                logger.warning(f"Candle {i} has negative volume, skipping")
                continue

            # Check high >= low and high >= open/close, low <= open/close
            if candle["high"] < candle["low"]:
                logger.warning(f"Candle {i} has high < low, skipping")
                continue

            if candle["high"] < candle["open"] or candle["high"] < candle["close"]:
                logger.warning(f"Candle {i} has high below open/close, skipping")
                continue

            if candle["low"] > candle["open"] or candle["low"] > candle["close"]:
                logger.warning(f"Candle {i} has low above open/close, skipping")
                continue

            # Check close_time > open_time (candle should have duration)
            if close_time <= open_time:
                logger.warning(f"Candle {i} has close_time <= open_time, skipping")
                continue

            # Store validated candle with normalized fields
            validated_candle = {
                "open_time": candle["open_time"],
                "close_time": candle["close_time"],
                "timestamp": _format_timestamp(candle["close_time"]),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
                "volume": float(candle["volume"]),
                "quote_volume": candle.get("quote_volume", candle["close"] * candle["volume"]),
                "trades": int(candle.get("trades", 0)),
                "taker_buy_base_volume": candle.get("taker_buy_base_volume", 0.0),
                "taker_buy_quote_volume": candle.get("taker_buy_quote_volume", 0.0),
            }
            validated.append(validated_candle)

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Candle {i} validation error: {e}, skipping")
            continue

    return validated


def _format_timestamp(close_time: int | float) -> str:
    """Format a Unix timestamp (ms) to ISO 8601 UTC string."""
    try:
        dt = datetime.fromtimestamp(close_time / 1000, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, OSError):
        return ""


def get_next_candle_boundary(timeframe: str) -> int:
    """Calculate the next candle boundary timestamp (ms) for the given timeframe.

    Returns the start time of the next complete candle interval.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    timestamp = now.timestamp() * 1000  # ms

    # Timeframe to minutes mapping
    timeframe_minutes = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "3d": 4320,
        "1w": 10080,
    }

    minutes = timeframe_minutes.get(timeframe, 60)

    # Calculate the boundary: round down to the nearest interval
    # Then add one interval to get the next boundary
    millis_per_minute = 60 * 1000
    millis_per_interval = minutes * millis_per_minute

    # Round down to nearest boundary
    boundary = (timestamp // millis_per_interval) * millis_per_interval

    # Next boundary = current boundary + interval
    next_boundary = boundary + millis_per_interval

    return int(next_boundary)


def is_candle_complete(candle_close_time: int, server_time: int | None = None) -> bool:
    """Determine if a candle has completed based on Binance server time.

    A candle is eligible for storage only when:
    candle.close_time < binance_server_time

    Args:
        candle_close_time: The candle's close time in milliseconds
        server_time: Binance server time in milliseconds (uses current time if None)

    Returns:
        True if the candle is complete, False if still open
    """
    if server_time is None:
        # Use current time as fallback (not ideal but functional)
        from datetime import datetime, timezone
        server_time = int(datetime.now(timezone.utc).timestamp() * 1000)

    return candle_close_time < server_time


def fetch_historical_candles(
    symbol: str,
    timeframe: str,
    limit: int = 1000,
    server_time: int | None = None
) -> Tuple[List[Dict[str, Any]], str | None]:
    """Fetch historical candlestick data from Binance API.

    Uses the existing Binance connection infrastructure.
    For public market data, uses the public market-data endpoint.
    Do not unnecessarily introduce API credentials where not required.

    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        timeframe: Candle interval (e.g., '5m')
        limit: Maximum number of candles to retrieve (default: 1000)
        server_time: Optional pre-fetched server time in ms

    Returns:
        (candles_list, error_message) tuple. candles_list is empty if error.
    """
    import time
    import urllib.request
    import json

    base_url = 'https://testnet.binance.vision' if server_time is None else None

    # Binance public kline/candlestick endpoint
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit={limit}"

    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            data = json.loads(raw.decode("utf-8"))

    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch candles for {symbol}/{timeframe}: {e}")
        return [], f"API request failed: {e}"
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse candle data for {symbol}/{timeframe}: {e}")
        return [], f"Invalid API response: {e}"
    except Exception as e:
        logger.error(f"Unexpected error fetching candles for {symbol}/{timeframe}: {e}")
        return [], f"Unexpected error: {e}"

    # Parse Binance response into candle dicts
    # Binance returns: [open_time, open, high, low, close, volume, close_time, quote_asset_volume,
    #                   number_of_trades, taker_buy_base_volume, taker_buy_quote_volume, ignore]
    candles: List[Dict[str, Any]] = []

    for entry in data:
        try:
            candle = {
                "open_time": int(entry[0]),       # Open time (ms)
                "open": float(entry[1]),          # Open price
                "high": float(entry[2]),          # High price
                "low": float(entry[3]),           # Low price
                "close": float(entry[4]),         # Close price
                "volume": float(entry[5]),        # Base asset volume
                "close_time": int(entry[6]),      # Close time (ms)
                "quote_volume": float(entry[7]),  # Quote asset volume
                "trades": int(entry[8]),          # Number of trades
                "taker_buy_base_volume": float(entry[9]),  # Taker buy base volume
                "taker_buy_quote_volume": float(entry[10]),  # Taker buy quote volume
            }
            candles.append(candle)
        except (ValueError, IndexError, TypeError) as e:
            logger.warning(f"Failed to parse candle entry: {e}, skipping: {entry}")
            continue

    logger.info(f"Fetched {len(candles)} valid candles for {symbol}/{timeframe}")
    return candles, None


def update_candle_data(symbol: str, timeframe: str, server_time: int | None = None) -> Dict[str, Any]:
    """Update candle data for a symbol/timeframe combination.

    Full workflow:
    1. Load existing data (or start fresh)
    2. Fetch new candles from Binance (incremental)
    3. Validate candles (only complete ones)
    4. Merge with existing data (deduplication)
    5. Trim to max 1000 candles
    6. Save to JSON
    7. Return summary

    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        timeframe: Candle interval (e.g., '5m')
        server_time: Optional pre-fetched server time in ms

    Returns:
        Dict with update summary including:
        - success: bool
        - candles_loaded: int
        - new_candles: int
        - duplicates_skipped: int
        - error: str | None
    """
    summary: Dict[str, Any] = {
        "success": False,
        "candles_loaded": 0,
        "new_candles": 0,
        "duplicates_skipped": 0,
        "error": None,
    }

    # Step 1: Load existing data
    existing_data, load_success = load_candles(symbol, timeframe)
    if not load_success:
        # No existing data - will start fresh
        existing_candles = []
    else:
        existing_candles = existing_data.get("candles", [])

    # Step 2: Fetch new candles
    # Use incremental approach: if we have existing data, fetch from the latest timestamp
    # Otherwise fetch 1000 historical candles
    if existing_candles:
        # We have existing data - determine latest close time to fetch incrementally
        latest_close = max(c.get("close_time", 0) for c in existing_candles)
        # Fetch candles starting after the latest close time
        # Binance doesn't support "from" parameter easily, so we fetch limit and filter
        new_candles_raw, fetch_error = fetch_historical_candles(symbol, timeframe, limit=500, server_time=server_time)

        if fetch_error:
            summary["error"] = fetch_error
            return summary

        # A newer Binance response can still contain the currently open candle.
        new_candles = [
            candle
            for candle in new_candles_raw
            if candle.get("close_time", 0) > latest_close
            and is_candle_complete(candle["close_time"], server_time)
        ]
    else:
        # No existing data - fetch 1000 historical candles
        new_candles_raw, fetch_error = fetch_historical_candles(symbol, timeframe, limit=1000, server_time=server_time)

        if fetch_error:
            summary["error"] = fetch_error
            return summary

        # Validate: only keep completed candles
        new_candles = [
            c for c in new_candles_raw
            if is_candle_complete(c["close_time"], server_time)
        ]

    summary["candles_loaded"] = len(new_candles_raw)

    # Step 3: Validate new candles (already done in fetch, but double-check)
    # Step 4: Merge with existing data
    merged = merge_candles(existing_candles, new_candles)

    # Count statistics
    duplicates_skipped = len(new_candles_raw) - len(new_candles)
    summary["duplicates_skipped"] = duplicates_skipped
    summary["new_candles"] = len(new_candles)

    # Step 5: Trim to max 1000 (already handled in merge_candles)
    # Step 6: Save to JSON
    save_success = save_candles(symbol, timeframe, merged)
    if not save_success:
        summary["error"] = "Failed to save candle data"
        return summary

    summary["success"] = True
    summary["candles_loaded"] = len(merged)

    logger.info(f"Updated candle data for {symbol}/{timeframe}: "
                f"{summary['new_candles']} new, {summary['duplicates_skipped']} duplicates skipped, "
                f"total: {summary['candles_loaded']} candles")

    return summary