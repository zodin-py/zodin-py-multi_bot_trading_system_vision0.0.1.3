"""Orchestrate explicitly requested, JSON-configured coin analyses."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.config import config
from backend.News_card.news_service import collect_news, get_news_items
from backend.candles.manager import load_candles, update_candle_data
from backend.services.strategy_service import STRATEGY_LABELS, StrategyAnalysisService

logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = {"indicators", "news", "strategies", "summary"}
SUPPORTED_STRATEGIES = set(STRATEGY_LABELS)


class AnalysisRequestError(ValueError):
    """Raised when an analysis request does not match the supported API contract."""


class RuleConfigurationError(ValueError):
    """Raised when the external analysis rule file is missing or invalid."""


class AnalysisDataError(RuntimeError):
    """Raised when a required data source cannot provide usable data."""


class AnalysisService:
    """Load current rules, run their supported actions in order, and persist results."""

    _history_lock = threading.Lock()

    def __init__(
        self,
        indicator_service: Any,
        *,
        strategy_service: StrategyAnalysisService | None = None,
        rules_path: Path | None = None,
        history_path: Path | None = None,
        candle_loader: Callable[..., Any] = load_candles,
        candle_updater: Callable[..., Any] = update_candle_data,
        news_collector: Callable[..., Any] = collect_news,
        news_item_loader: Callable[..., Any] = get_news_items,
    ) -> None:
        backend_dir = Path(__file__).resolve().parents[1]
        self._indicator_service = indicator_service
        self._strategy_service = strategy_service or StrategyAnalysisService()
        self._rules_path = rules_path or backend_dir / "regeln.json"
        self._history_path = history_path or backend_dir / "data" / "analysis_history.jsonl"
        self._candle_loader = candle_loader
        self._candle_updater = candle_updater
        self._news_collector = news_collector
        self._news_item_loader = news_item_loader

    def analyze(
        self,
        symbol: Any,
        timeframe: Any,
        strategies: Any,
    ) -> dict[str, Any]:
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_timeframe = self._validate_timeframe(timeframe)
        selected_strategies = self._validate_strategies(strategies)
        rules, rule_version, rules_hash = self._load_rules()
        if (
            not selected_strategies
            and any(rule["action"] == "strategies" for rule in rules)
        ):
            raise AnalysisRequestError(
                "Wähle mindestens eine Strategie für diesen Analyseauftrag aus."
            )

        started_at = datetime.now(timezone.utc).isoformat()
        context: dict[str, Any] = {
            "symbol": normalized_symbol,
            "timeframe": normalized_timeframe,
            "strategies": selected_strategies,
            "steps": [],
        }
        for rule in rules:
            step_record: dict[str, Any] = {
                "step": rule["step"],
                "action": rule["action"],
                "title": rule["title"],
                "instructions": rule["instructions"],
            }
            try:
                result = self._execute_action(rule["action"], context)
                step_record["status"] = (
                    "partial" if result.get("status") == "partial" else "completed"
                )
                step_record["result"] = result
            except AnalysisDataError as error:
                logger.warning(
                    "Analysis step %s (%s) unavailable: %s",
                    rule["step"],
                    rule["action"],
                    error,
                )
                step_record["status"] = "failed"
                step_record["error"] = str(error)
            except Exception:
                logger.exception(
                    "Unexpected analysis step failure at step %s (%s)",
                    rule["step"],
                    rule["action"],
                )
                step_record["status"] = "failed"
                step_record["error"] = (
                    "Der Analyseschritt konnte wegen eines internen Fehlers nicht ausgeführt werden."
                )
            context["steps"].append(step_record)

        failed_steps = [
            step["step"] for step in context["steps"] if step["status"] != "completed"
        ]
        analysis = {
            "symbol": normalized_symbol,
            "timeframe": normalized_timeframe,
            "strategies": selected_strategies,
            "rules_version": rule_version,
            "rules_sha256": rules_hash,
            "started_at": started_at,
            "status": "partial" if failed_steps else "completed",
            "failed_steps": failed_steps,
            "steps": context["steps"],
            "summary": self._latest_summary(context["steps"]),
        }
        self._append_history(analysis)
        return analysis

    @staticmethod
    def _normalize_symbol(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AnalysisRequestError("symbol muss ein unterstützter Coin sein.")
        symbol = value.strip().upper()
        if "/" in symbol and not re.fullmatch(r"[A-Z0-9]+/USDT", symbol):
            raise AnalysisRequestError("symbol muss ein unterstützter Coin sein.")
        symbol = symbol.replace("/", "")
        if not symbol.endswith(config.DEFAULT_QUOTE):
            symbol += config.DEFAULT_QUOTE
        if symbol not in config.COINS:
            raise AnalysisRequestError(f"Coin '{value}' wird nicht unterstützt.")
        return symbol

    @staticmethod
    def _validate_timeframe(value: Any) -> str:
        if not isinstance(value, str) or value not in config.TIMEFRAMES:
            raise AnalysisRequestError(
                f"timeframe muss einer dieser Werte sein: {', '.join(config.TIMEFRAMES)}."
            )
        return value

    @staticmethod
    def _validate_strategies(value: Any) -> list[str]:
        if not isinstance(value, list):
            raise AnalysisRequestError("strategies muss eine Liste von Strategie-IDs sein.")
        if any(not isinstance(strategy, str) for strategy in value):
            raise AnalysisRequestError("Jede Strategie-ID muss eine Zeichenkette sein.")
        if len(set(value)) != len(value):
            raise AnalysisRequestError("Eine Strategie darf nicht mehrfach ausgewählt werden.")
        unknown = [strategy for strategy in value if strategy not in SUPPORTED_STRATEGIES]
        if unknown:
            raise AnalysisRequestError(
                f"Unbekannte Strategie-ID(s): {', '.join(unknown)}."
            )
        return list(value)

    def _load_rules(self) -> tuple[list[dict[str, Any]], int, str]:
        try:
            contents = self._rules_path.read_bytes()
        except OSError as error:
            raise RuleConfigurationError(
                f"Regeldatei konnte nicht gelesen werden: {error.strerror or error}."
            ) from error
        try:
            payload = json.loads(contents.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuleConfigurationError(
                f"Regeldatei enthält ungültiges UTF-8 oder JSON: {error}."
            ) from error

        if not isinstance(payload, dict):
            raise RuleConfigurationError("Die Regeldatei muss ein JSON-Objekt enthalten.")
        version = payload.get("version")
        if type(version) is not int or version < 1:
            raise RuleConfigurationError("'version' muss eine positive Ganzzahl sein.")
        rules = payload.get("analysis_rules")
        if not isinstance(rules, list) or not rules:
            raise RuleConfigurationError(
                "'analysis_rules' muss eine nicht leere Liste sein."
            )

        validated_rules: list[dict[str, Any]] = []
        previous_step = 0
        for index, rule in enumerate(rules):
            location = f"analysis_rules[{index}]"
            if not isinstance(rule, dict):
                raise RuleConfigurationError(f"{location} muss ein JSON-Objekt sein.")
            step = rule.get("step")
            if type(step) is not int or step <= previous_step:
                raise RuleConfigurationError(
                    f"{location}.step muss eine positive, eindeutig aufsteigende Ganzzahl sein."
                )
            previous_step = step
            action = rule.get("action")
            if not isinstance(action, str) or action not in SUPPORTED_ACTIONS:
                raise RuleConfigurationError(
                    f"{location}.action muss eine unterstützte Aktion sein: "
                    f"{', '.join(sorted(SUPPORTED_ACTIONS))}."
                )
            title = rule.get("title")
            if not isinstance(title, str) or not title.strip():
                raise RuleConfigurationError(f"{location}.title darf nicht leer sein.")
            instructions = rule.get("instructions")
            if not isinstance(instructions, str) or not instructions.strip():
                raise RuleConfigurationError(
                    f"{location}.instructions darf nicht leer sein."
                )
            validated_rules.append({
                "step": step,
                "action": action,
                "title": title.strip(),
                "instructions": instructions.strip(),
            })

        return validated_rules, version, hashlib.sha256(contents).hexdigest()

    def _execute_action(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        if action == "indicators":
            return self._analyze_indicators(context["symbol"], context["timeframe"])
        if action == "news":
            return self._analyze_news(context["symbol"])
        if action == "strategies":
            return self._analyze_strategies(context)
        if action == "summary":
            return self._summarize(context["steps"])
        raise RuleConfigurationError(f"Nicht unterstützte Analyseaktion: {action}.")

    def _analyze_indicators(self, symbol: str, timeframe: str) -> dict[str, Any]:
        indicators = self._indicator_service.get_indicators(symbol, timeframe)
        if not isinstance(indicators, dict):
            raise AnalysisDataError("Indikatorwerte konnten nicht abgerufen werden.")

        values = {
            key: self._last_finite(indicators.get(key))
            for key in ("rsi", "macd", "signal", "hist", "ema")
        }
        rsi = values["rsi"]
        macd = values["macd"]
        macd_signal = values["signal"]
        rsi_config = config.INDICATOR_PARAMS.get("rsi", {})
        oversold = float(rsi_config.get("oversold", 30))
        overbought = float(rsi_config.get("overbought", 70))
        if rsi is not None and rsi <= oversold:
            signal = "BUY"
            reason = f"RSI liegt bei oder unter {oversold:g} (überverkauft)."
        elif rsi is not None and rsi >= overbought:
            signal = "SELL"
            reason = f"RSI liegt bei oder über {overbought:g} (überkauft)."
        elif macd is not None and macd_signal is not None and macd != macd_signal:
            signal = "BUY" if macd > macd_signal else "SELL"
            reason = "MACD liegt über bzw. unter seiner Signallinie."
        elif any(value is not None for value in values.values()):
            signal = "HOLD"
            reason = "Die verfügbaren Indikatoren liefern keine eindeutige Richtung."
        else:
            signal = "INCONCLUSIVE"
            reason = "Für den gewählten Coin und Timeframe liegen keine Indikatorwerte vor."
        return {
            "signal": signal,
            "reason": reason,
            "values": values,
            "rsi_thresholds": {
                "oversold": oversold,
                "overbought": overbought,
            },
            "timeframe": indicators.get("timeframe", timeframe),
            "symbol": indicators.get("symbol", symbol),
        }

    def _analyze_news(self, symbol: str) -> dict[str, Any]:
        collection = self._news_collector()
        items = self._news_item_loader()
        if not isinstance(items, list):
            raise AnalysisDataError("Der News-Service lieferte kein gültiges Ergebnis.")

        base = symbol.removesuffix(config.DEFAULT_QUOTE)
        aliases = {
            "BTC": ("BITCOIN",),
            "ETH": ("ETHEREUM",),
            "BNB": ("BINANCE COIN",),
            "SOL": ("SOLANA",),
            "ADA": ("CARDANO",),
            "XRP": ("RIPPLE",),
            "DOGE": ("DOGECOIN",),
        }.get(base, ())
        matcher = re.compile(
            r"(?<![A-Z0-9])(?:"
            + "|".join(re.escape(term) for term in (base, symbol, *aliases))
            + r")(?![A-Z0-9])",
            re.IGNORECASE,
        )
        relevant = []
        for item in items:
            if not isinstance(item, dict):
                continue
            searchable = " ".join(
                str(item.get(key, ""))
                for key in ("title", "summary", "topics")
            )
            if not matcher.search(searchable):
                continue
            relevant.append({
                key: item.get(key)
                for key in ("title", "source", "url", "summary", "date")
                if item.get(key) is not None
            })
            if len(relevant) == 20:
                break
        return {
            "collected_new": collection.get("total_new", 0)
            if isinstance(collection, dict)
            else 0,
            "matching_items": relevant,
            "sentiment": "not_assessed",
            "note": "Meldungen werden angezeigt; eine automatische Sentimentbewertung ist nicht implementiert.",
        }

    def _analyze_strategies(self, context: dict[str, Any]) -> dict[str, Any]:
        candles = context.get("candles")
        if candles is None:
            update = self._candle_updater(context["symbol"], context["timeframe"])
            if not isinstance(update, dict) or not update.get("success"):
                message = (
                    update.get("error")
                    if isinstance(update, dict)
                    else None
                )
                raise AnalysisDataError(
                    message or "Kerzendaten konnten nicht aktualisiert werden."
                )
            candle_data, success = self._candle_loader(
                context["symbol"], context["timeframe"]
            )
            candles = candle_data.get("candles", []) if success and isinstance(candle_data, dict) else []
            if not candles:
                raise AnalysisDataError(
                    "Für den gewählten Coin und Timeframe sind keine Kerzen verfügbar."
                )
            context["candles"] = candles
        results = self._strategy_service.analyze(context["strategies"], candles)
        return {
            "results": results,
            "status": "partial"
            if any(result.get("status") == "failed" for result in results)
            else "completed",
        }

    @staticmethod
    def _last_finite(values: Any) -> float | None:
        if not isinstance(values, list) or not values:
            return None
        try:
            value = float(values[-1])
        except (TypeError, ValueError):
            return None
        return value if math.isfinite(value) else None

    @staticmethod
    def _summarize(steps: list[dict[str, Any]]) -> dict[str, Any]:
        signals: list[str] = []
        incomplete_steps = [
            step["step"] for step in steps if step.get("status") != "completed"
        ]
        for step in steps:
            if step.get("status") not in ("completed", "partial"):
                continue
            if step.get("action") not in ("indicators", "strategies"):
                continue
            result = step.get("result")
            if not isinstance(result, dict):
                continue
            signal = result.get("signal")
            if signal in ("BUY", "SELL", "HOLD"):
                signals.append(signal)
            for strategy in result.get("results", []):
                if isinstance(strategy, dict) and strategy.get("signal") in (
                    "BUY",
                    "SELL",
                    "HOLD",
                ):
                    signals.append(strategy["signal"])

        counts = {signal: signals.count(signal) for signal in ("BUY", "SELL", "HOLD")}
        if counts["BUY"] > counts["SELL"]:
            signal = "BUY"
        elif counts["SELL"] > counts["BUY"]:
            signal = "SELL"
        elif counts["BUY"] or counts["SELL"] or counts["HOLD"]:
            signal = "HOLD"
        else:
            signal = "INCONCLUSIVE"
        reason = (
            "Deterministische Zusammenfassung der ausgeführten Indikator- und Strategie-Signale; "
            "kein Trade wurde ausgeführt."
        )
        if incomplete_steps:
            reason += (
                " Fehlgeschlagene Schritte: "
                + ", ".join(str(step) for step in incomplete_steps)
                + "."
            )
        return {
            "signal": signal,
            "signal_counts": counts,
            "reason": reason,
            "incomplete_steps": incomplete_steps,
        }

    @classmethod
    def _latest_summary(cls, steps: list[dict[str, Any]]) -> dict[str, Any]:
        summaries = [
            step["result"]
            for step in steps
            if step.get("action") == "summary"
            and step.get("status") == "completed"
            and isinstance(step.get("result"), dict)
        ]
        return summaries[-1] if summaries else cls._summarize(steps)

    def _append_history(self, analysis: dict[str, Any]) -> None:
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        with self._history_lock:
            with self._history_path.open("a", encoding="utf-8") as history_file:
                json.dump(analysis, history_file, ensure_ascii=False, allow_nan=False)
                history_file.write("\n")
                history_file.flush()

