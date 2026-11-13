"""Hammer Candlestick Pattern Analyzer.

Provides Hammer candlestick pattern detection.
Implements the BaseAnalyzer interface for modular integration.

A Hammer is a bullish reversal pattern that forms after a decline.
Characteristics:
- Lower shadow at least 2x the body length
- Very small or no upper shadow
- Body at the top of the trading range
- Can be bullish (close > open) or bearish (close < open), bullish is more common
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


class HammerPattern(BaseAnalyzer):
    """Hammer candlestick pattern analyzer.

    The Hammer is a bullish reversal pattern that forms after a decline.
    It has a small body at the upper end of the trading range and a long lower shadow
    that is at least 2x the body length.

    ID: pattern.hammer
    """

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "id": "pattern.hammer",
            "name": "Hammer",
            "category": "pattern",
            "description": "Bullish reversal candlestick pattern - hammer formation",
            "icon": "key",
            "config_fields": ["body_ratio_threshold", "lower_shadow_ratio"],
            "default_config": {"body_ratio_threshold": 0.3, "lower_shadow_ratio": 2.0},
        }

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "body_ratio_threshold": 0.3,  # Body must be <= 30% of total range
            "lower_shadow_ratio": 2.0,    # Lower shadow must be >= 2x body
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Hammer pattern configuration.

        Returns list of error messages (empty if valid).
        """
        errors: List[str] = []

        body_ratio = config.get("body_ratio_threshold", 0.3)
        if not isinstance(body_ratio, (int, float)) or body_ratio <= 0 or body_ratio > 1:
            errors.append("body_ratio_threshold must be between 0 and 1")

        lower_shadow = config.get("lower_shadow_ratio", 2.0)
        if not isinstance(lower_shadow, (int, float)) or lower_shadow < 1:
            errors.append("lower_shadow_ratio must be >= 1")

        return errors

    def analyze(self, context: AnalysisContext, config: Dict[str, Any]) -> AnalysisResult:
        """Run Hammer pattern detection on the given context.

        For Current mode: Check only the latest closed candle for hammer formation.
        For History mode: Examine all historical candles for hammer patterns.

        Args:
            context: AnalysisContext with candles, mode, symbol, timeframe
            config: Configuration dict with body_ratio_threshold and lower_shadow_ratio

        Returns:
            AnalysisResult with hammer pattern signals
        """
        body_ratio_threshold = config.get("body_ratio_threshold", 0.3)
        lower_shadow_ratio = config.get("lower_shadow_ratio", 2.0)

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
            signal = self._is_hammer(candle, body_ratio_threshold, lower_shadow_ratio)
            if signal:
                latest_price = float(candle.get("close", candle.get("open", 0)))
                signals.append({
                    "timestamp": candle.get("close_time", 0),
                    "candle_index": context.latest_closed_index,
                    "type": "pattern",
                    "direction": "bullish",
                    "price": latest_price,
                    "title": "Hammer Pattern",
                    "description": "Bullish Hammer pattern detected",
                    "details": {
                        "body_ratio": signal.get("body_ratio", 0),
                        "lower_shadow_ratio": signal.get("lower_shadow_ratio", 0),
                        "total_range": signal.get("total_range", 0),
                    },
                })

        elif context.mode == "history":
            # Check all historical candles
            for i, candle in enumerate(candles):
                signal = self._is_hammer(candle, body_ratio_threshold, lower_shadow_ratio)
                if signal:
                    price = float(candle.get("close", candle.get("open", 0)))
                    signals.append({
                        "timestamp": candle.get("close_time", 0),
                        "candle_index": i,
                        "type": "pattern",
                        "direction": "bullish",
                        "price": price,
                        "title": "Hammer Pattern",
                        "description": "Bullish Hammer pattern detected",
                        "details": {
                            "body_ratio": signal.get("body_ratio", 0),
                            "lower_shadow_ratio": signal.get("lower_shadow_ratio", 0),
                            "total_range": signal.get("total_range", 0),
                        },
                    })

        return AnalysisResult(
            analyzer_id="pattern.hammer",
            symbol=context.symbol,
            timeframe=context.timeframe,
            mode=context.mode,
            status="success" if signals else "no_signal",
            signals=signals,
            series=[],
        )

    def _is_hammer(
        self,
        candle: Dict[str, Any],
        body_ratio_threshold: float,
        lower_shadow_ratio: float,
    ) -> Optional[Dict[str, Any]]:
        """Determine if a candle forms a Hammer pattern.

        A Hammer has:
        - Lower shadow at least 2x the body length
        - Body at the top of the trading range
        - Very small or no upper shadow
        - Body ratio (body / total_range) <= threshold

        Returns dict with pattern details if hammer, None otherwise.
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

            # Lower shadow: from low to min(open, close)
            lower_shadow = min(open_price, close_price) - low

            # Upper shadow: from max(open, close) to high
            upper_shadow = high - max(open_price, close_price)

            # Hammer conditions:
            # 1. Lower shadow >= 2x body height
            # 2. Body ratio <= threshold (body is small relative to range)
            # 3. Upper shadow is minimal (ideally 0 or very small)
            if (
                lower_shadow >= body_height * lower_shadow_ratio
                and body_ratio <= body_ratio_threshold
                and upper_shadow < body_height * 0.5  # Upper shadow should be much smaller than body
            ):
                # Determine lower shadow ratio relative to body
                lower_shadow_ratio_calc = lower_shadow / body_height if body_height > 0 else 0

                return {
                    "body_ratio": round(body_ratio, 4),
                    "lower_shadow_ratio": round(lower_shadow_ratio_calc, 4),
                    "total_range": round(total_range, 4),
                    "open": open_price,
                    "close": close_price,
                    "low": low,
                    "high": high,
                }

            return None

        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Hammer pattern validation error: {e}")
            return None