"""Hourly trading risk checks and persistent risk state."""

from __future__ import annotations

import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from backend import config

logger = logging.getLogger(__name__)
BERLIN = ZoneInfo("Europe/Berlin")


def berlin_now() -> datetime:
    return datetime.now(BERLIN)


def berlin_today_start(now: datetime | None = None) -> datetime:
    current = now or berlin_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=BERLIN)
    return current.astimezone(BERLIN).replace(hour=0, minute=0, second=0, microsecond=0)


def _trade_timestamp(trade: dict[str, Any]) -> datetime | None:
    value = trade.get("timestamp")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc).astimezone(BERLIN)
    for key in ("datetime", "close_time", "open_time"):
        raw = trade.get(key)
        if not isinstance(raw, str) or not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=BERLIN)
            return parsed.astimezone(BERLIN)
        except ValueError:
            continue
    return None


def get_usdc_balance(wallet: dict[str, Any]) -> float:
    balances = wallet.get("balances")
    if isinstance(balances, list):
        for balance in balances:
            if str(balance.get("asset", "")).upper() in ("USDC", "USDT"):
                try:
                    return float(balance.get("free", 0)) + float(balance.get("locked", 0))
                except (TypeError, ValueError):
                    continue
    try:
        return float(wallet.get("usdc", wallet.get("USDC", wallet.get("usdt", 0))))
    except (TypeError, ValueError):
        return 0.0


def calculate_daily_performance(
    trades: Iterable[dict[str, Any]],
    usdc_balance: float,
    now: datetime | None = None,
) -> dict[str, float]:
    """Calculate today's realized profit/loss, including fees."""
    start = berlin_today_start(now)
    grouped: dict[str, deque[tuple[float, float]]] = defaultdict(deque)
    profit = 0.0
    loss = 0.0
    buy_cost = 0.0

    today_trades = []
    for trade in trades:
        timestamp = _trade_timestamp(trade)
        if timestamp is not None and timestamp >= start:
            today_trades.append(trade)

    for trade in sorted(today_trades, key=lambda item: _trade_timestamp(item) or start):
        symbol = str(trade.get("symbol") or "")
        side = str(trade.get("side", "")).lower()
        price = float(trade.get("price", 0) or 0)
        amount = float(trade.get("amount", 0) or 0)

        fee = trade.get("fee")
        fee_cost = 0.0
        if isinstance(fee, dict):
            try:
                fee_cost = float(fee.get("cost", 0) or 0)
            except (TypeError, ValueError):
                fee_cost = 0.0

        explicit_pnl = trade.get("pnl")
        if explicit_pnl is not None:
            try:
                pnl = float(explicit_pnl) - fee_cost
            except (TypeError, ValueError):
                pnl = 0.0
            if pnl > 0:
                profit += pnl
            elif pnl < 0:
                loss += abs(pnl)
            continue

        if side == "buy":
            if price > 0 and amount > 0:
                grouped[symbol].append((amount, price))
                buy_cost += price * amount + fee_cost
        elif side == "sell":
            remaining = amount
            realized = -fee_cost
            while remaining > 0 and grouped[symbol]:
                bought_amount, bought_price = grouped[symbol][0]
                matched = min(remaining, bought_amount)
                realized += (price - bought_price) * matched
                remaining -= matched
                bought_amount -= matched
                if bought_amount <= 1e-12:
                    grouped[symbol].popleft()
                else:
                    grouped[symbol][0] = (bought_amount, bought_price)
            if realized > 0:
                profit += realized
            elif realized < 0:
                loss += abs(realized)

    denominator = buy_cost if buy_cost > 0 else max(usdc_balance, 0.01)
    return {
        "profit": round(profit, 8),
        "loss": round(loss, 8),
        "performance_percent": round(((profit - loss) / denominator) * 100, 8),
        "profit_percent": round((profit / denominator) * 100, 8),
        "loss_percent": round((loss / denominator) * 100, 8),
    }


class RiskStateStore:
    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            project_root = Path(__file__).resolve().parents[2]
            path = project_root / "trades" / "risk_state.json"
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"status": "RUNNING", "manual_stop": False, "stop_until": None, "stop_reasons": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError) as error:
            logger.error("Could not read risk state: %s", error)
        return {"status": "RUNNING", "manual_stop": False, "stop_until": None, "stop_reasons": []}

    def save(self, state: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)


class RiskManager:
    def __init__(self, state_store: RiskStateStore | None = None) -> None:
        self.state_store = state_store or RiskStateStore()

    def evaluate(
        self,
        usdc_balance: float,
        profit: float,
        loss: float,
        performance_percent: float,
        profit_percent: float,
        loss_percent: float,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        state = self.state_store.load()
        if state.get("manual_stop"):
            return {"should_stop": True, "status": "STOPPED", "reasons": ["Manueller Stop ist aktiv"], "manual_stop": True}

        stop_until = state.get("stop_until")
        today = (now or berlin_now()).astimezone(BERLIN).date().isoformat()
        if stop_until:
            try:
                stopped_date = datetime.fromisoformat(stop_until).date()
                if stopped_date >= (now or berlin_now()).astimezone(BERLIN).date():
                    return {"should_stop": True, "status": "STOPPED", "reasons": state.get("stop_reasons") or ["Tägliches Risikolimit erreicht"], "manual_stop": False}
            except (TypeError, ValueError):
                pass

        reasons = []
        if usdc_balance > float(getattr(config.config, "RISK_USDC_STOP", 25.0)):
            reasons.append(f"USDC-Wallet-Bestand {usdc_balance:.2f} USDC ist größer als 25.00 USDC")
        if profit_percent > float(getattr(config.config, "RISK_DAILY_PROFIT_STOP_PERCENT", 6.0)):
            reasons.append(f"Tagesgewinn {profit_percent:.2f}% ist größer als 6.00%")
        if loss_percent > float(getattr(config.config, "RISK_DAILY_LOSS_STOP_PERCENT", 3.0)):
            reasons.append(f"Tagesverlust {loss_percent:.2f}% ist größer als 3.00%")

        if reasons:
            state.update({"status": "STOPPED", "manual_stop": False, "stop_until": today, "stop_reasons": reasons})
            self.state_store.save(state)
            return {"should_stop": True, "status": "STOPPED", "reasons": reasons, "manual_stop": False}

        state.update({"status": "RUNNING", "stop_reasons": []})
        if not state.get("manual_stop"):
            state["stop_until"] = None
        self.state_store.save(state)
        return {"should_stop": False, "status": "RUNNING", "reasons": [], "manual_stop": False}

    def manual_stop(self, reason: str = "Manueller Stop") -> dict[str, Any]:
        state = self.state_store.load()
        state.update({"status": "STOPPED", "manual_stop": True, "stop_reasons": [reason]})
        self.state_store.save(state)
        return state

    def manual_resume(self) -> dict[str, Any]:
        state = self.state_store.load()
        state.update({"status": "RUNNING", "manual_stop": False, "stop_reasons": [], "stop_until": None})
        self.state_store.save(state)
        return state
