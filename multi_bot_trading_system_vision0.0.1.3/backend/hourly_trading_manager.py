"""Central hourly orchestrator for risk checks and coin analysis."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from backend import config
from backend.services.risk_manager import (
    BERLIN,
    RiskManager,
    calculate_daily_performance,
    berlin_now,
    get_usdc_balance,
)

logger = logging.getLogger(__name__)


class HourlyTradingManager:
    def __init__(
        self,
        wallet_service: Any = None,
        trade_history_service: Any = None,
        analysis_engine: Any = None,
        risk_manager: RiskManager | None = None,
        log_path: Path | None = None,
    ) -> None:
        if wallet_service is None:
            from backend.services.wallet_service import WalletService
            wallet_service = WalletService()
        if trade_history_service is None:
            from backend.services.trade_history_service import TradeHistoryService
            trade_history_service = TradeHistoryService()

        self.wallet_service = wallet_service
        self.trade_history_service = trade_history_service
        self.analysis_engine = analysis_engine
        self.risk_manager = risk_manager or RiskManager()
        project_root = Path(__file__).resolve().parents[1]
        self.project_root = project_root
        self.log_path = log_path or (project_root / "trades" / "hourly_runs.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _append_log(self, entry: dict[str, Any]) -> None:
        entry["timestamp"] = berlin_now().isoformat()
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def load_selected_coins(self) -> list[str]:
        path = self.project_root / "backend" / "News_card" / "today-coins.json"
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            logger.error("Could not load coin selection skill output: %s", error)
            return []
        coins = []
        for item in data.get("coins", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            symbol = str(item.get("symbol", "")).strip().upper()
            if symbol:
                coins.append(symbol if symbol.endswith("USDT") else f"{symbol}{config.DEFAULT_QUOTE}")
        return coins

    def analyze_coins(self, coins: list[str]) -> dict[str, dict[str, Any]]:
        if not coins or self.analysis_engine is None:
            return {coin: {"signal": "NO_TRADE", "result": None} for coin in coins}

        from backend.candles.manager import load_candles

        selected = [
            {"analyzer_id": "indicator.rsi", "mode": "current", "config": {"length": 14, "source": "close", "overbought": 70, "oversold": 30}},
            {"analyzer_id": "indicator.macd", "mode": "current", "config": {}},
            {"analyzer_id": "indicator.ema", "mode": "current", "config": {"period": 20}},
        ]
        results = {}
        for coin in coins:
            try:
                candle_data, success = load_candles(coin, "1h")
                candles = candle_data.get("candles", []) if success and candle_data else []
                if not candles:
                    results[coin] = {"signal": "NO_TRADE", "result": {"error": "No candle data"}}
                    continue
                result = self.analysis_engine.run_analysis(
                    symbol=coin,
                    timeframe="1h",
                    mode="current",
                    selected=selected,
                    all_candles=candles,
                )
                bullish = 0
                bearish = 0
                for analyzer_result in result.get("results", {}).values():
                    for signal in analyzer_result.get("signals", []):
                        direction = str(signal.get("type", signal.get("signal", ""))).upper()
                        if "BUY" in direction or "BULL" in direction:
                            bullish += 1
                        elif "SELL" in direction or "BEAR" in direction:
                            bearish += 1
                signal = "BUY" if bullish > bearish and bullish > 0 else ("HOLD" if bearish == 0 else "NO_TRADE")
                results[coin] = {"signal": signal, "result": result}
            except Exception as error:
                logger.exception("Analysis failed for %s", coin)
                results[coin] = {"signal": "NO_TRADE", "result": {"error": str(error)}}
        return results

    def run_once(self) -> dict[str, Any]:
        if not self._lock.acquire(blocking=False):
            entry = {"status": "ERROR", "error": "A previous hourly execution is still running"}
            self._append_log(entry)
            return entry

        try:
            entry: dict[str, Any] = {
                "status": "RISK_CHECK",
                "wallet_usdc": None,
                "daily_profit": None,
                "daily_loss": None,
                "daily_performance_percent": None,
                "selected_coins": [],
                "analysis_results": {},
                "executed_orders": [],
                "stop_reasons": [],
                "errors": [],
            }
            try:
                wallet = self.wallet_service.get_wallet_sync()
                if wallet is None or "error" in wallet:
                    raise RuntimeError(wallet.get("error", "Wallet data is unavailable") if wallet else "Wallet data is unavailable")
                usdc_balance = get_usdc_balance(wallet)

                trades = self.trade_history_service.get_trade_history_sync(limit=1000)
                performance = calculate_daily_performance(trades, usdc_balance)
                entry.update({
                    "wallet_usdc": usdc_balance,
                    "daily_profit": performance["profit"],
                    "daily_loss": performance["loss"],
                    "daily_performance_percent": performance["performance_percent"],
                    "profit_percent": performance["profit_percent"],
                    "loss_percent": performance["loss_percent"],
                })

                risk = self.risk_manager.evaluate(
                    usdc_balance=usdc_balance,
                    profit=performance["profit"],
                    loss=performance["loss"],
                    performance_percent=performance["performance_percent"],
                    profit_percent=performance["profit_percent"],
                    loss_percent=performance["loss_percent"],
                )
                if risk["should_stop"]:
                    entry["status"] = "STOPPED"
                    entry["stop_reasons"] = risk["reasons"]
                    logger.warning("Trading stopped: %s", "; ".join(risk["reasons"]))
                    self._append_log(entry)
                    return entry

                entry["status"] = "COIN_SELECTION"
                coins = self.load_selected_coins()
                entry["selected_coins"] = coins
                if not coins:
                    entry["status"] = "RUNNING"
                    entry["analysis_results"] = {}
                    self._append_log(entry)
                    return entry

                entry["status"] = "ANALYSIS"
                analysis = self.analyze_coins(coins)
                entry["analysis_results"] = analysis

                # Order execution is intentionally disabled in this project state.
                entry["status"] = "TRADING"
                entry["executed_orders"] = []
                entry["errors"].append("Order execution disabled: only analysis signals are generated")
                entry["status"] = "RUNNING"
            except Exception as error:
                logger.exception("Hourly trading manager failed")
                entry["status"] = "ERROR"
                entry["errors"].append(str(error))
            self._append_log(entry)
            return entry
        finally:
            self._lock.release()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        interval = int(getattr(config.config, "HOURLY_INTERVAL_SECONDS", 3600))

        def loop() -> None:
            while not self._stop_event.wait(interval):
                if not self._lock.locked():
                    self.run_once()

        self._thread = threading.Thread(target=loop, name="hourly-trading-manager", daemon=True)
        self._thread.start()
        logger.info("Hourly trading manager scheduler started")

    def stop(self) -> None:
        self._stop_event.set()
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1)


def hourly_trading_manager() -> dict[str, Any]:
    """Module-level compatibility entry point for the hourly specification."""
    return HourlyTradingManager().run_once()
