"""EMA Indicator Analyzer — Exponential Moving Average.

Provides Exponential Moving Average technical indicator analysis.
Implements the BaseAnalyzer interface for modular integration.

Features:
- Configurable period
- Supports Current and History modes
- Returns EMA series for chart display
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


class EMAIndicator(BaseAnalyzer):
    """EMA (Exponential Moving Average) indicator analyzer.

    Calculates EMA using pandas ewm (exponential weighted moving average).
    Supports both Current mode (signal on latest closed candle) and History mode
    (signals on all historical candles).

    ID: indicator.ema
    """

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "id": "indicator.ema",
            "name": "EMA",
            "category": "indicator",
            "description": "Exponential Moving Average technical indicator",
            "icon": "trending_up",
            "config_fields": ["period", "source"],
            "default_config": {"period": 20, "source": "close"},
        }

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "period": 20,
            "source": "close",
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate EMA configuration.

        Returns list of error messages (empty if valid).
        """
        errors: List[str] = []

        period = config.get("period", 20)
        if not isinstance(period, int) or period < 1:
            errors.append("period must be a positive integer")

        source = config.get("source", "close")
        valid_sources = ["open", "high", "low", "close"]
        if source not in valid_sources:
            errors.append(f"source must be one of {valid_sources}")

        return errors

    def analyze(self, context: AnalysisContext, config: Dict[str, Any]) -> AnalysisResult:
        """Run EMA analysis on the given context.

        For Current mode: EMA is computed and the latest value is checked against
        the latest closed candle price.

        For History mode: EMA series is computed for all candles and returned.

        Args:
            context: AnalysisContext with candles, mode, symbol, timeframe
            config: Configuration dict with period and source

        Returns:
            AnalysisResult with EMA series
        """
        import pandas as pd

        period = config.get("period", 20)
        source = config.get("source", "close")

        candles = context.candles
        if not candles or len(candles) < period + 5:
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

            if len(price_series) < period + 5:
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
            # Compute EMA - note: we use all available data, but only return last 20
            ema = df["close"].ewm(span=period, adjust=False).mean()

            # Return series (last 20 values)
            ema_series = ema.dropna().tolist()[-20:]

            # For Current mode, also determine if there's a signal
            signals: List[Dict[str, Any]] = []
            if context.mode == "current" and len(ema_series) > 0:
                latest_ema = ema_series[-1]
                # Get the latest closed candle's price
                latest_candle = candles[context.latest_closed_index]
                latest_price = float(latest_candle.get("close", latest_candle.get("open", 0)))

                # Signal: price crossed above EMA (bullish) or below EMA (bearish)
                prev_ema = ema_series[-2] if len(ema_series) > 1 else latest_ema
                if latest_price > latest_ema and latest_price > prev_ema:
                    signals.append({
                        "timestamp": latest_candle.get("close_time", 0),
                        "candle_index": context.latest_closed_index,
                        "type": "ema_cross",
                        "direction": "bullish",
                        "price": latest_price,
                        "title": "EMA Bullish Cross",
                        "description": f"Price crossed above {period}-period EMA",
                        "details": {"ema_value": latest_ema, "period": period},
                    })
                elif latest_price < latest_ema and latest_price < prev_ema:
                    signals.append({
                        "timestamp": latest_candle.get("close_time", 0),
                        "candle_index": context.latest_closed_index,
                        "type": "ema_cross",
                        "direction": "bearish",
                        "price": latest_price,
                        "title": "EMA Bearish Cross",
                        "description": f"Price crossed below {period}-period EMA",
                        "details": {"ema_value": latest_ema, "period": period},
                    })

            return AnalysisResult(
                analyzer_id="indicator.ema",
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="success",
                signals=signals,
                series=ema_series,
            )

        except Exception as e:
            logger.error(f"EMA analysis error for {context.symbol}: {e}")
            return AnalysisResult(
                analyzer_id="indicator.ema",
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="error",
                signals=[],
                series=[],
            )