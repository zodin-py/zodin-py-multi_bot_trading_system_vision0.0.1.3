"""RSI Indicator Analyzer — Relative Strength Index.

Provides RSI (Relative Strength Index) technical indicator analysis.
Implements the BaseAnalyzer interface for modular integration.

Features:
- Configurable period and source (default: close, length 14)
- Supports Current and History modes
- Returns RSI values and buy/sell signals
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


class RSIIndicator(BaseAnalyzer):
    """RSI (Relative Strength Index) indicator analyzer.

    Calculates RSI using Wilder's smoothing method.
    Supports both Current mode (signal on latest closed candle) and History mode
    (signals on all historical candles with RSI levels).

    ID: indicator.rsi
    """

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "id": "indicator.rsi",
            "name": "RSI",
            "category": "indicator",
            "description": "Relative Strength Index momentum oscillator",
            "icon": "trending_lines",
            "config_fields": ["length", "source", "overbought", "oversold"],
            "default_config": {"length": 14, "source": "close", "overbought": 70, "oversold": 30},
        }

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "length": 14,
            "source": "close",
            "overbought": 70,
            "oversold": 30,
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate RSI configuration.

        Returns list of error messages (empty if valid).
        """
        errors: List[str] = []

        length = config.get("length", 14)
        if not isinstance(length, int) or length < 1:
            errors.append("length must be a positive integer")

        source = config.get("source", "close")
        valid_sources = ["open", "high", "low", "close"]
        if source not in valid_sources:
            errors.append(f"source must be one of {valid_sources}")

        overbought = config.get("overbought", 70)
        if not isinstance(overbought, (int, float)) or overbought > 100:
            errors.append("overbought must be a number <= 100")

        oversold = config.get("oversold", 30)
        if not isinstance(oversold, (int, float)) or oversold < 0:
            errors.append("oversold must be a number >= 0")

        if isinstance(overbought, (int, float)) and isinstance(oversold, (int, float)):
            if overbought <= oversold:
                errors.append("overbought must be greater than oversold")

        return errors

    def analyze(self, context: AnalysisContext, config: Dict[str, Any]) -> AnalysisResult:
        """Run RSI analysis on the given context.

        For Current mode: RSI is computed for the latest closed candle.
        If RSI is oversold (<= oversold), generate a bullish signal.
        If RSI is overbought (>= overbought), generate a bearish signal.

        For History mode: RSI series is computed for all candles,
        and signals are generated wherever RSI crosses levels.

        Args:
            context: AnalysisContext with candles, mode, symbol, timeframe
            config: Configuration dict with length, source, overbought, oversold

        Returns:
            AnalysisResult with RSI values and signals
        """
        import pandas as pd

        length = config.get("length", 14)
        source = config.get("source", "close")
        overbought = config.get("overbought", 70)
        oversold = config.get("oversold", 30)

        candles = context.candles
        if not candles or len(candles) < length + 5:
            return AnalysisResult(
                analyzer_id=context.symbol,
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="error",
                signals=[],
                series=[],
            )

        # Extract price series
        try:
            price_series = []
            for c in candles:
                if source == "open":
                    price_series.append(float(c.get("open", 0)))
                elif source == "high":
                    price_series.append(float(c.get("high", 0)))
                elif source == "low":
                    price_series.append(float(c.get("low", 0)))
                else:
                    price_series.append(float(c.get("close", 0)))

            if len(price_series) < length + 5:
                return AnalysisResult(
                    analyzer_id=context.symbol,
                    symbol=context.symbol,
                    timeframe=context.timeframe,
                    mode=context.mode,
                    status="error",
                    signals=[],
                    series=[],
                )

            df = pd.DataFrame({"close": price_series})

            # Compute RSI using Wilder's smoothing
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Return series (last 20 values, dropna first)
            rsi_series = rsi.dropna().tolist()[-20:]

            # For Current mode, check RSI level on latest closed candle
            signals: List[Dict[str, Any]] = []
            if context.mode == "current" and len(rsi_series) > 0:
                latest_rsi = rsi_series[-1]
                latest_candle = candles[context.latest_closed_index]

                # Determine price from latest closed candle
                latest_price = float(latest_candle.get("close", 0))

                # Generate signal based on RSI level
                if latest_rsi <= oversold:
                    # Oversold - bullish signal
                    signals.append({
                        "timestamp": latest_candle.get("close_time", 0),
                        "candle_index": context.latest_closed_index,
                        "type": "rsi_oversold",
                        "direction": "bullish",
                        "price": latest_price,
                        "title": "RSI Oversold",
                        "description": f"RSI ({latest_rsi:.1f}) is oversold (<= {oversold})",
                        "details": {
                            "rsi_value": round(latest_rsi, 2),
                            "length": length,
                            "oversold": oversold,
                            "overbought": overbought,
                        },
                    })
                elif latest_rsi >= overbought:
                    # Overbought - bearish signal
                    signals.append({
                        "timestamp": latest_candle.get("close_time", 0),
                        "candle_index": context.latest_closed_index,
                        "type": "rsi_overbought",
                        "direction": "bearish",
                        "price": latest_price,
                        "title": "RSI Overbought",
                        "description": f"RSI ({latest_rsi:.1f}) is overbought (>= {overbought})",
                        "details": {
                            "rsi_value": round(latest_rsi, 2),
                            "length": length,
                            "oversold": oversold,
                            "overbought": overbought,
                        },
                    })

            # For History mode, find RSI level crossovers
            if context.mode == "history" and len(rsi_series) > 1:
                for i in range(1, len(rsi_series)):
                    prev_rsi = rsi_series[i - 1]
                    curr_rsi = rsi_series[i]

                    candle = candles[i] if i < len(candles) else candles[-1]
                    candle_price = float(candle.get("close", 0))

                    # Bullish crossover: RSI crosses above oversold
                    if prev_rsi < oversold and curr_rsi >= oversold:
                        signals.append({
                            "timestamp": candle.get("close_time", 0) if i < len(candles) else 0,
                            "candle_index": i,
                            "type": "rsi_bullish_cross",
                            "direction": "bullish",
                            "price": candle_price,
                            "title": "RSI Bullish Crossover",
                            "description": f"RSI crossed above oversold level ({prev_rsi:.1f} → {curr_rsi:.1f})",
                            "details": {
                                "rsi_value": round(curr_rsi, 2),
                                "oversold": oversold,
                                "crossover_type": "above_oversold",
                            },
                        })

                    # Bearish crossover: RSI crosses below overbought
                    if prev_rsi > overbought and curr_rsi <= overbought:
                        signals.append({
                            "timestamp": candle.get("close_time", 0) if i < len(candles) else 0,
                            "candle_index": i,
                            "type": "rsi_bearish_cross",
                            "direction": "bearish",
                            "price": candle_price,
                            "title": "RSI Bearish Crossover",
                            "description": f"RSI crossed below overbought level ({prev_rsi:.1f} → {curr_rsi:.1f})",
                            "details": {
                                "rsi_value": round(curr_rsi, 2),
                                "overbought": overbought,
                                "crossover_type": "below_overbought",
                            },
                        })

            return AnalysisResult(
                analyzer_id="indicator.rsi",
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="success",
                signals=signals,
                series=rsi_series,
            )

        except Exception as e:
            logger.error(f"RSI analysis error for {context.symbol}: {e}")
            return AnalysisResult(
                analyzer_id="indicator.rsi",
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="error",
                signals=[],
                series=[],
            )