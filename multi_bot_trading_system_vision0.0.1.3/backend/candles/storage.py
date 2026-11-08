#!/usr/bin/env python3
"""Candle Storage Module - Handles JSON read/write with atomic operations.

Provides consistent storage operations for the candle manager module.
Handles atomic writes, recovery from corrupted files, and directory management.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .manager import get_candle_file_path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CANDLE_DATA_DIR_NAME = "data/candles"
DEFAULT_MAX_CANDLES = 1000


# ---------------------------------------------------------------------------
# Directory Management
# ---------------------------------------------------------------------------

def get_candle_data_dir() -> Path:
    """Return the operating system path for candle data storage.

    Relative to the project root (where this package is imported from).
    Will create the directory if it doesn't exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / CANDLE_DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def ensure_candle_data_dir() -> Path:
    """Ensure the candle data directory exists, creating if needed.

    Returns the Path object for the candle data directory.
    """
    data_dir = get_candle_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


# ---------------------------------------------------------------------------
# File Operations
# ---------------------------------------------------------------------------

def load_candle_file(symbol: str, timeframe: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Load a candle JSON file for the given symbol/timeframe.

    Returns:
        (data, success) tuple. data is None if file not found or invalid.
        success is False if file not found, True if loaded successfully.
    """
    file_path = get_candle_file_path(symbol, timeframe)

    if not file_path.exists():
        return None, False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None, False
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None, False


def save_candle_file_atomic(
    symbol: str,
    timeframe: str,
    data: Dict[str, Any],
    max_candles: int = DEFAULT_MAX_CANDLES
) -> bool:
    """Save candle data to JSON file using atomic write procedure.

    Atomic write procedure:
    1. Build the complete updated JSON object
    2. Write it to a temporary file
    3. Flush and close the temporary file
    4. Replace the original file atomically
    5. Preserve the previous valid file if the operation fails

    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        timeframe: Candle interval (e.g., '5m')
        data: Candle data dict with 'metadata' and 'candles' keys
        max_candles: Maximum number of candles to retain (default: 1000)

    Returns:
        True if save succeeded, False otherwise
    """
    file_path = get_candle_file_path(symbol, timeframe)
    data_dir = file_path.parent

    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Trim candles to max limit before saving
    candles = data.get("candles", [])
    if len(candles) > max_candles:
        # Keep the newest max_candles candles
        candles = candles[-max_candles:]
        data["candles"] = candles
        data["metadata"]["candle_count"] = len(candles)
        logger.info(f"Trimmed candle data from {len(candles) + (len(data.get('candles', [])) - len(candles))} "
                    f"to {max_candles} candles")

    # Atomic write: write to temp file, then replace
    try:
        # Write to temporary file first
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        # Atomically replace original file
        os.replace(tmp_path, file_path)

        logger.info(f"Atomically saved {len(candles)} candles to {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving candle file atomically: {e}")
        # Clean up temp file if it exists
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass
        return False


def save_candle_file(
    symbol: str,
    timeframe: str,
    data: Dict[str, Any],
    max_candles: int = DEFAULT_MAX_CANDLES
) -> bool:
    """Save candle data to JSON file (non-atomic convenience wrapper).

    Note: Does not use the atomic write procedure. Use save_candle_file_atomic
    for production use where data integrity is critical.

    Args:
        symbol: Trading symbol
        timeframe: Candle interval
        data: Candle data dict
        max_candles: Maximum number of candles to retain

    Returns:
        True if save succeeded, False otherwise
    """
    file_path = get_candle_file_path(symbol, timeframe)
    data_dir = file_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Trim candles to max limit before saving
        candles = data.get("candles", [])
        if len(candles) > max_candles:
            candles = candles[-max_candles:]
            data["candles"] = candles
            data["metadata"]["candle_count"] = len(candles)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(candles)} candles to {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving candle file: {e}")
        return False


# ---------------------------------------------------------------------------
# Recovery & Corruption Handling
# ---------------------------------------------------------------------------

def recover_corrupted_file(
    symbol: str,
    timeframe: str,
    fallback_data: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Attempt to recover a corrupted or invalid candle JSON file.

    Recovery strategy:
    1. Try to parse what we can from the existing file
    2. If recovery fails, use fallback data (if provided)
    3. If no fallback, return empty candle data structure

    Args:
        symbol: Trading symbol
        timeframe: Candle interval
        fallback_data: Optional fallback candle data structure

    Returns:
        Recovered or fallback candle data dict
    """
    file_path = get_candle_file_path(symbol, timeframe)

    if not fallback_data:
        fallback_data = _empty_candle_data()

    if not file_path.exists():
        logger.warning(f"No candle file at {file_path}, using fallback")
        return fallback_data

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to parse the file
        data = json.loads(content)

        # Validate minimum structure
        if not isinstance(data, dict):
            logger.warning(f"Recovered data from {file_path} is not a dict, using fallback")
            return fallback_data

        # Check for required keys
        has_metadata = "metadata" in data
        has_candles = "candles" in data

        if has_metadata and has_candles:
            # Validate candles list
            candles = data.get("candles", [])
            if not isinstance(candles, list):
                logger.warning(f"Candles in {file_path} is not a list, using fallback")
                return fallback_data

            # Count valid candles
            valid_count = sum(1 for c in candles if isinstance(c, dict) and "open_time" in c)

            if valid_count > 0:
                logger.info(f"Recovered {valid_count} valid candles from {file_path}")
                return data
            else:
                logger.warning(f"No valid candles found in {file_path}, using fallback")
                return fallback_data
        else:
            # Missing required keys, try to salvage what we can
            logger.warning(f"Recovered data from {file_path} missing required keys, using fallback")
            return fallback_data

    except json.JSONDecodeError as e:
        logger.error(f"Cannot recover corrupted file {file_path}: {e}, using fallback")
        return fallback_data
    except Exception as e:
        logger.error(f"Unexpected error recovering {file_path}: {e}, using fallback")
        return fallback_data


def _empty_candle_data() -> Dict[str, Any]:
    """Return an empty candle data structure."""
    from ..candles.manager import _empty_candle_data as empty_manager
    return empty_manager()