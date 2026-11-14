"""MACD Indicator Analyzer — Moving Average Convergence Divergence.

Provides MACD (Moving Average Convergence Divergence) technical indicator analysis.
Implements the BaseAnalyzer interface for modular integration.

Features:
- Configurable fast/slow/signal periods
- Returns MACD line, signal line, and histogram
- Supports Current and History modes
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.analyzers.base_analyzer import (
    BaseAnalyzer,
    AnalysisContext,
    AnalysisResult,
)


logger = logging.getLogger(__name__)


class MACDIndicator(BaseAnalyzer):
    """MACD (Moving Average Convergence Divergence) indicator analyzer.

    Calculates MACD using exponential moving averages:
    - MACD line: fast EMA - slow EMA
    - Signal line: EMA of MACD line
    - Histogram: MACD line - Signal line

    ID: indicator.macd
    """

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "id": "indicator.macd",
            "name": "MACD",
            "category": "indicator",
            "description": "Moving Average Convergence Divergence trend-following indicator",
            "icon": "equalizer",
            "config_fields": ["fast_period", "slow_period", "signal_period"],
            "default_config": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
        }

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate MACD configuration.

        Returns list of error messages (empty if valid).
        """
        errors: List[str] = []

        fast_period = config.get("fast_period", 12)
        if not isinstance(fast_period, int) or fast_period < 1:
            errors.append("fast_period must be a positive integer")

        slow_period = config.get("slow_period", 26)
        if not isinstance(slow_period, int) or slow_period < 1:
            errors.append("slow_period must be a positive integer")

        signal_period = config.get("signal_period", 9)
        if not isinstance(signal_period, int) or signal_period < 1:
            errors.append("signal_period must be a positive integer")

        # Fast must be shorter than slow
        if (
            isinstance(fast_period, int)
            and isinstance(slow_period, int)
            and fast_period >= slow_period
        ):
            errors.append("fast_period must be less than slow_period")

        return errors

    def analyze(self, context: AnalysisContext, config: Dict[str, Any]) -> AnalysisResult:
        """Run MACD analysis on the given context.

        For Current mode: MACD values are computed and signal is generated
        based on crossovers of MACD line and signal line.

        For History mode: Full MACD series is computed for all candles,
        with signals at each crossover point.

        Args:
            context: AnalysisContext with candles, mode, symbol, timeframe
            config: Configuration dict with fast_period, slow_period, signal_period

        Returns:
            AnalysisResult with MACD line, signal line, histogram, and signals
        """
        import pandas as pd

        fast_period = config.get("fast_period", 12)
        slow_period = config.get("slow_period", 26)
        signal_period = config.get("signal_period", 9)

        candles = context.candles
        if not candles or len(candles) < slow_period + signal_period + 10:
            return AnalysisResult(
                analyzer_id=context.symbol,
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="error",
                signals=[],
                series=[],
            )

        # Extract close price series
        try:
            closes = [float(c.get("close", 0)) for c in candles]

            if len(closes) < slow_period + signal_period + 10:
                return AnalysisResult(
                    analyzer_id=context.symbol,
                    symbol=context.symbol,
                    timeframe=context.timeframe,
                    mode=context.mode,
                    status="error",
                    signals=[],
                    series=[],
                )

            df = pd.DataFrame({"close": closes})

            # Compute MACD
            fast_ema = df["close"].ewm(span=fast_period, adjust=False).mean()
            slow_ema = df["close"].ewm(span=slow_period, adjust=False).mean()
            macd_line = fast_ema - slow_ema
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            histogram = macd_line - signal_line

            # Get last 20 values
            macd_series = macd_line.dropna().tolist()[-20:]
            signal_series = signal_line.dropna().tolist()[-20:]
            hist_series = histogram.dropna().tolist()[-20:]

            # For Current mode, check for crossover signal
            signals: List[Dict[str, Any]] = []
            if context.mode == "current" and len(macd_series) > 1:
                latest_macd = macd_series[-1]
                latest_signal = signal_series[-1]
                prev_macd = macd_series[-2]
                prev_signal = signal_series[-2]

                # Bullish crossover: MACD crosses above signal
                if prev_macd <= prev_signal and latest_macd > latest_signal:
                    latest_candle = candles[context.latest_closed_index]
                    latest_price = float(latest_candle.get("close", 0))

                    signals.append({
                        "timestamp": latest_candle.get("close_time", 0),
                        "candle_index": context.latest_closed_index,
                        "type": "macd_bullish_cross",
                        "direction": "bullish",
                        "price": latest_price,
                        "title": "MACD Bullish Crossover",
                        "description": "MACD line crossed above signal line",
                        "details": {
                            "macd_value": round(latest_macd, 4),
                            "signal_value": round(latest_signal, 4),
                            "histogram": round(latest_macd - latest_signal, 4),
                        },
                    })

                # Bearish crossover: MACD crosses below signal
                elif prev_macd >= prev_signal and latest_macd < latest_signal:
                    latest_candle = candles[context.latest_closed_index]
                    latest_price = float(latest_candle.get("close", 0))

                    signals.append({
                        "timestamp": latest_candle.get("close_time", 0),
                        "candle_index": context.latest_closed_index,
                        "type": "macd_bearish_cross",
                        "direction": "bearish",
                        "price": latest_price,
                        "title": "MACD Bearish Crossover",
                        "description": "MACD line crossed below signal line",
                        "details": {
                            "macd_value": round(latest_macd, 4),
                            "signal_value": round(latest_signal, 4),
                            "histogram": round(latest_macd - latest_signal, 4),
                        },
                    })

            # For History mode, find all crossover points
            if context.mode == "history" and len(macd_series) > 1:
                for i in range(1, len(macd_series)):
                    prev_m = macd_series[i - 1]
                    curr_m = macd_series[i]
                    prev_s = signal_series[i - 1]
                    curr_s = signal_series[i]

                    candle = candles[i] if i < len(candles) else candles[-1]
                    candle_price = float(candle.get("close", 0))

                    # Bullish crossover
                    if prev_m <= prev_s and curr_m > curr_s:
                        signals.append({
                            "timestamp": candle.get("close_time", 0) if i < len(candles) else 0,
                            "candle_index": i,
                            "type": "macd_bullish_cross",
                            "direction": "bullish",
                            "price": candle_price,
                            "title": "MACD Bullish Crossover",
                            "description": f"MACD line crossed above signal line at candle {i}",
                            "details": {
                                "macd_value": round(curr_m, 4),
                                "signal_value": round(curr_s, 4),
                            },
                        })

                    # Bearish crossover
                    if prev_m >= prev_s and curr_m < curr_s:
                        signals.append({
                            "timestamp": candle.get("close_time", 0) if i < len(candles) else 0,
                            "candle_index": i,
                            "type": "macd_bearish_cross",
                            "direction": "bearish",
                            "price": candle_price,
                            "title": "MACD Bearish Crossover",
                            "description": f"MACD line crossed below signal line at candle {i}",
                            "details": {
                                "macd_value": round(curr_m, 4),
                                "signal_value": round(curr_s, 4),
                            },
                        })

            return AnalysisResult(
                analyzer_id="indicator.macd",
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="success",
                signals=signals,
                series={"macd": macd_series, "signal": signal_series, "histogram": hist_series},
            )

        except Exception as e:
            logger.error(f"MACD analysis error for {context.symbol}: {e}")
            return AnalysisResult(
                analyzer_id="indicator.macd",
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="error",
                signals=[],
                series=[],
            )