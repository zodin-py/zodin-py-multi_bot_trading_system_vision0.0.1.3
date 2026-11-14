"""Doji Candlestick Pattern Analyzer.

Provides Doji candlestick pattern detection.
Implements the BaseAnalyzer interface for modular integration.

A Doji is a neutral pattern where the open and close are virtually equal,
indicating market indecision. The body is very small relative to the total range.

ID: pattern.doji
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


class DojiPattern(BaseAnalyzer):
    """Doji candlestick pattern analyzer.

    A Doji forms when the open and close prices are nearly equal,
    indicating market indecision. The body is very small relative to
    the total price range.

    ID: pattern.doji
    """

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "id": "pattern.doji",
            "name": "Doji",
            "category": "pattern",
            "description": "Neutral doji candlestick pattern - market indecision",
            "icon": "circle",
            "config_fields": ["body_ratio_threshold"],
            "default_config": {"body_ratio_threshold": 0.1},
        }

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "body_ratio_threshold": 0.1,  # Body must be <= 10% of total range
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Doji pattern configuration.

        Returns list of error messages (empty if valid).
        """
        errors: List[str] = []

        body_ratio = config.get("body_ratio_threshold", 0.1)
        if not isinstance(body_ratio, (int, float)) or body_ratio <= 0 or body_ratio > 1:
            errors.append("body_ratio_threshold must be between 0 and 1")

        return errors

    def analyze(self, context: AnalysisContext, config: Dict[str, Any]) -> AnalysisResult:
        """Run Doji pattern detection on the given context.

        For Current mode: Check only the latest closed candle for doji formation.
        For History mode: Examine all historical candles for doji patterns.

        Args:
            context: AnalysisContext with candles, mode, symbol, timeframe
            config: Configuration dict with body_ratio_threshold

        Returns:
            AnalysisResult with doji pattern signals
        """
        body_ratio_threshold = config.get("body_ratio_threshold", 0.1)

        candles = context.candles
        if not candles:
            return AnalysisResult(
                analyzer_id=context.symbol,
                symbol=context.symbol,
                timeframe=context.timeframe,
                mode=context.mode,
                status="error",
                signals=[],
                series=[],
            )

        signals: List[Dict[str, Any]] = []

        if context.mode == "current":
            # Check only the latest closed candle
            if context.latest_closed_index >= len(candles):
                return AnalysisResult(
                    analyzer_id=context.symbol,
                    symbol=context.symbol,
                    timeframe=context.timeframe,
                    mode=context.mode,
                    status="error",
                    signals=[],
                    series=[],
                )

            candle = candles[context.latest_closed_index]
            signal = self._is_doji(candle, body_ratio_threshold)
            if signal:
                price = float(candle.get("close", candle.get("open", 0)))
                signals.append({
                    "timestamp": candle.get("close_time", 0),
                    "candle_index": context.latest_closed_index,
                    "type": "pattern",
                    "direction": "neutral",
                    "price": price,
                    "title": "Doji Pattern",
                    "description": "Doji pattern detected - market indecision",
                    "details": {
                        "body_ratio": signal.get("body_ratio", 0),
                        "total_range": signal.get("total_range", 0),
                    },
                })

        elif context.mode == "history":
            # Check all historical candles
            for i, candle in enumerate(candles):
                signal = self._is_doji(candle, body_ratio_threshold)
                if signal:
                    price = float(candle.get("close", candle.get("open", 0)))
                    signals.append({
                        "timestamp": candle.get("close_time", 0),
                        "candle_index": i,
                        "type": "pattern",
                        "direction": "neutral",
                        "price": price,
                        "title": "Doji Pattern",
                        "description": "Doji pattern detected - market indecision",
                        "details": {
                            "body_ratio": signal.get("body_ratio", 0),
                            "total_range": signal.get("total_range", 0),
                        },
                    })

        return AnalysisResult(
            analyzer_id="pattern.doji",
            symbol=context.symbol,
            timeframe=context.timeframe,
            mode=context.mode,
            status="success" if signals else "no_signal",
            signals=signals,
            series=[],
        )

    def _is_doji(
        self,
        candle: Dict[str, Any],
        body_ratio_threshold: float,
    ) -> Optional[Dict[str, Any]]:
        """Determine if a candle forms a Doji pattern.

        A Doji has:
        - Very small body relative to total range
        - Body ratio (body / total_range) <= threshold

        Returns dict with pattern details if doji, None otherwise.
        """
        try:
            open_price = float(candle.get("open", 0))
            close_price = float(candle.get("close", 0))
            high = float(candle.get("high", 0))
            low = float(candle.get("low", 0))

            body_height = abs(close_price - open_price)
            total_range = high - low

            if total_range == 0:
                return None

            # Body ratio: body / total range
            body_ratio = body_height / total_range

            # Doji condition: body is very small relative to total range
            if body_ratio <= body_ratio_threshold:
                return {
                    "body_ratio": round(body_ratio, 4),
                    "total_range": round(total_range, 4),
                    "open": open_price,
                    "close": close_price,
                    "low": low,
                    "high": high,
                }

            return None

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Doji pattern validation error: {e}")
            return None