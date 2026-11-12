"""Deterministic, non-executing strategy analyses for completed OHLCV candles."""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

STRATEGY_LABELS = {
    "sr": "Support und Resistance",
    "smc": "Smart Money Concepts",
    "harmonic": "Harmonische Muster",
    "trend": "Trend",
}


class StrategyAnalysisService:
    """Run transparent heuristic strategies without placing or modifying orders."""

    def analyze(
        self, strategy_ids: list[str], candles: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        valid_candles = self._valid_candles(candles)
        results = []
        for strategy_id in strategy_ids:
            analyzer = {
                "sr": self._analyze_support_resistance,
                "smc": self._analyze_smc,
                "harmonic": self._analyze_harmonic,
                "trend": self._analyze_trend,
            }.get(strategy_id)
            if analyzer is None:
                results.append({
                    "strategy": strategy_id,
                    "name": strategy_id,
                    "status": "failed",
                    "signal": "INCONCLUSIVE",
                    "reason": "Unbekannte Strategie.",
                    "data": {},
                })
                continue
            try:
                results.append(analyzer(valid_candles))
            except (ArithmeticError, IndexError, KeyError, TypeError, ValueError):
                logger.exception("Strategy analysis failed for %s", strategy_id)
                results.append({
                    "strategy": strategy_id,
                    "name": STRATEGY_LABELS[strategy_id],
                    "status": "failed",
                    "signal": "INCONCLUSIVE",
                    "reason": "Die Strategie konnte mit den verfügbaren Kerzen nicht berechnet werden.",
                    "data": {},
                })
        return results

    @staticmethod
    def _valid_candles(candles: list[dict[str, Any]]) -> list[dict[str, float]]:
        valid: list[dict[str, float]] = []
        for candle in candles:
            try:
                parsed = {
                    key: float(candle[key])
                    for key in ("open", "high", "low", "close")
                }
            except (KeyError, TypeError, ValueError):
                continue
            if not all(math.isfinite(value) for value in parsed.values()):
                continue
            if parsed["high"] < parsed["low"]:
                continue
            valid.append(parsed)
        return valid

    @staticmethod
    def _result(
        strategy_id: str,
        signal: str,
        reason: str,
        data: dict[str, Any],
        *,
        status: str = "completed",
    ) -> dict[str, Any]:
        return {
            "strategy": strategy_id,
            "name": STRATEGY_LABELS[strategy_id],
            "status": status,
            "signal": signal,
            "reason": reason,
            "data": data,
        }

    @staticmethod
    def _pivots(
        candles: list[dict[str, float]], left: int = 2, right: int = 2
    ) -> list[tuple[int, str, float]]:
        pivots: list[tuple[int, str, float]] = []
        for index in range(left, len(candles) - right):
            high = candles[index]["high"]
            low = candles[index]["low"]
            neighbors = candles[index - left:index] + candles[index + 1:index + right + 1]
            is_high = all(high > candle["high"] for candle in neighbors)
            is_low = all(low < candle["low"] for candle in neighbors)
            if is_high == is_low:
                continue
            kind = "high" if is_high else "low"
            value = high if is_high else low
            if pivots and pivots[-1][1] == kind:
                previous = pivots[-1]
                if (kind == "high" and value > previous[2]) or (
                    kind == "low" and value < previous[2]
                ):
                    pivots[-1] = (index, kind, value)
            else:
                pivots.append((index, kind, value))
        return pivots

    @classmethod
    def _analyze_support_resistance(
        cls, candles: list[dict[str, float]]
    ) -> dict[str, Any]:
        strategy_id = "sr"
        if len(candles) < 7:
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Für bestätigte Swing-Pivots liegen zu wenige Kerzen vor.",
                {"candles_used": len(candles)},
                status="inconclusive",
            )

        recent = candles[-200:]
        pivots = cls._pivots(recent)
        price = recent[-1]["close"]
        supports = [value for _, kind, value in pivots if kind == "low" and value < price]
        resistances = [value for _, kind, value in pivots if kind == "high" and value > price]
        support = max(supports) if supports else None
        resistance = min(resistances) if resistances else None
        support_distance = (price - support) / price if support is not None and price else None
        resistance_distance = (resistance - price) / price if resistance is not None and price else None
        support_distance_for_comparison = (
            support_distance if support_distance is not None else math.inf
        )
        resistance_distance_for_comparison = (
            resistance_distance if resistance_distance is not None else math.inf
        )
        threshold = 0.01

        near_support = support_distance is not None and support_distance <= threshold
        near_resistance = resistance_distance is not None and resistance_distance <= threshold
        if near_support and (
            not near_resistance
            or support_distance_for_comparison < resistance_distance_for_comparison
        ):
            signal = "BUY"
            reason = "Der Schlusskurs liegt höchstens 1 % über dem nächsten bestätigten Pivot-Tief."
        elif near_resistance and (
            not near_support
            or resistance_distance_for_comparison < support_distance_for_comparison
        ):
            signal = "SELL"
            reason = "Der Schlusskurs liegt höchstens 1 % unter dem nächsten bestätigten Pivot-Hoch."
        elif near_support and near_resistance:
            signal = "HOLD"
            reason = "Unterstützung und Widerstand liegen ähnlich nahe; das Signal ist uneindeutig."
        else:
            signal = "HOLD"
            reason = "Der Schlusskurs liegt nicht innerhalb von 1 % eines bestätigten Pivot-Levels."

        return cls._result(
            strategy_id,
            signal,
            reason,
            {
                "last_close": price,
                "nearest_support": support,
                "nearest_resistance": resistance,
                "support_distance_percent": support_distance * 100 if support_distance is not None else None,
                "resistance_distance_percent": resistance_distance * 100 if resistance_distance is not None else None,
                "threshold_percent": 1.0,
                "candles_used": len(recent),
            },
        )

    @classmethod
    def _analyze_smc(cls, candles: list[dict[str, float]]) -> dict[str, Any]:
        strategy_id = "smc"
        if len(candles) < 3:
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Für die Fair-Value-Gap-Prüfung liegen zu wenige Kerzen vor.",
                {"candles_used": len(candles)},
                status="inconclusive",
            )

        price = candles[-1]["close"]
        start = max(0, len(candles) - 60)
        active_gap: dict[str, Any] | None = None
        for index in range(start, len(candles) - 2):
            first = candles[index]
            third = candles[index + 2]
            if first["high"] < third["low"] and first["high"] <= price <= third["low"]:
                active_gap = {
                    "direction": "bullish",
                    "low": first["high"],
                    "high": third["low"],
                    "formed_at_index": index + 2,
                }
            elif first["low"] > third["high"] and third["high"] <= price <= first["low"]:
                active_gap = {
                    "direction": "bearish",
                    "low": third["high"],
                    "high": first["low"],
                    "formed_at_index": index + 2,
                }

        if active_gap is None:
            return cls._result(
                strategy_id,
                "HOLD",
                "Der aktuelle Schlusskurs liegt in keiner erkannten Fair-Value-Gap-Zone.",
                {"last_close": price, "candles_scanned": len(candles) - start},
            )
        signal = "BUY" if active_gap["direction"] == "bullish" else "SELL"
        return cls._result(
            strategy_id,
            signal,
            f"Der Schlusskurs liegt in einer {active_gap['direction']} Fair-Value-Gap-Zone.",
            {"last_close": price, "fair_value_gap": active_gap},
        )

    @classmethod
    def _analyze_harmonic(cls, candles: list[dict[str, float]]) -> dict[str, Any]:
        strategy_id = "harmonic"
        pivots = cls._pivots(candles)
        if len(pivots) < 5:
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Es wurden nicht genügend bestätigte Swing-Punkte für ein XABCD-Muster gefunden.",
                {"confirmed_pivots": len(pivots)},
                status="inconclusive",
            )

        x, a, b, c, d = pivots[-5:]
        if [x[1], a[1], b[1], c[1], d[1]] not in (
            ["low", "high", "low", "high", "low"],
            ["high", "low", "high", "low", "high"],
        ):
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Die letzten fünf Swing-Punkte bilden keine alternierende XABCD-Struktur.",
                {"confirmed_pivots": len(pivots)},
                status="inconclusive",
            )

        xa = abs(a[2] - x[2])
        ab = abs(b[2] - a[2])
        bc = abs(c[2] - b[2])
        cd = abs(d[2] - c[2])
        if min(xa, ab, bc) <= 0:
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Die Swing-Punkte erlauben keine stabilen Fibonacci-Verhältnisse.",
                {},
                status="inconclusive",
            )
        ratios = {
            "ab_xa": ab / xa,
            "bc_ab": bc / ab,
            "cd_bc": cd / bc,
            "ad_xa": abs(d[2] - a[2]) / xa,
        }
        patterns: dict[str, tuple[tuple[float, float], ...]] = {
            "Gartley": ((0.55, 0.68), (0.382, 0.886), (1.27, 1.618), (0.72, 0.85)),
            "Bat": ((0.382, 0.50), (0.382, 0.886), (1.618, 2.618), (0.81, 0.96)),
            "Butterfly": ((0.72, 0.85), (0.382, 0.886), (1.618, 2.24), (1.20, 1.70)),
            "Crab": ((0.382, 0.618), (0.382, 0.886), (2.24, 3.618), (1.45, 1.80)),
        }
        matched_pattern = next(
            (
                name
                for name, ranges in patterns.items()
                if all(
                    lower <= ratio <= upper
                    for ratio, (lower, upper) in zip(ratios.values(), ranges)
                )
            ),
            None,
        )
        if matched_pattern is None:
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Die letzten fünf bestätigten Swing-Punkte erfüllen kein geprüftes XABCD-Fibonacci-Muster.",
                {"ratios": ratios, "confirmed_pivots": len(pivots)},
                status="inconclusive",
            )

        bullish = x[1] == "low"
        signal = "BUY" if bullish else "SELL"
        direction = "bullish" if bullish else "bearish"
        return cls._result(
            strategy_id,
            signal,
            f"Die Swing-Punkte entsprechen heuristisch einem {direction}en {matched_pattern}-Muster.",
            {
                "pattern": matched_pattern,
                "direction": direction,
                "ratios": ratios,
                "confirmed_pivots": len(pivots),
            },
        )

    @staticmethod
    def _ema(values: list[float], period: int) -> list[float]:
        multiplier = 2 / (period + 1)
        result = [values[0]]
        for value in values[1:]:
            result.append((value - result[-1]) * multiplier + result[-1])
        return result

    @classmethod
    def _analyze_trend(cls, candles: list[dict[str, float]]) -> dict[str, Any]:
        strategy_id = "trend"
        if len(candles) < 26:
            return cls._result(
                strategy_id,
                "INCONCLUSIVE",
                "Für den EMA-9/21-Trendvergleich liegen zu wenige Kerzen vor.",
                {"candles_used": len(candles)},
                status="inconclusive",
            )

        closes = [candle["close"] for candle in candles]
        fast_ema = cls._ema(closes, 9)
        slow_ema = cls._ema(closes, 21)
        slow_ema_slope = slow_ema[-1] - slow_ema[-6]
        if fast_ema[-1] > slow_ema[-1] and slow_ema_slope > 0:
            signal = "BUY"
            reason = "EMA 9 liegt über EMA 21 und EMA 21 steigt über die letzten fünf Kerzen."
        elif fast_ema[-1] < slow_ema[-1] and slow_ema_slope < 0:
            signal = "SELL"
            reason = "EMA 9 liegt unter EMA 21 und EMA 21 fällt über die letzten fünf Kerzen."
        else:
            signal = "HOLD"
            reason = "EMA-Ausrichtung und EMA-21-Richtung bestätigen keinen gemeinsamen Trend."

        return cls._result(
            strategy_id,
            signal,
            reason,
            {
                "last_close": closes[-1],
                "ema_9": fast_ema[-1],
                "ema_21": slow_ema[-1],
                "ema_21_change_5_candles": slow_ema_slope,
                "candles_used": len(candles),
            },
        )
