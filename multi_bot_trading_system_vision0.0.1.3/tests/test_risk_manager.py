from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from backend.services.risk_manager import (
    RiskManager,
    RiskStateStore,
    calculate_daily_performance,
)


def test_daily_performance_pairs_buy_and_sell_and_includes_fee():
    berlin = ZoneInfo("Europe/Berlin")
    now = datetime(2026, 11, 18, 12, 0, tzinfo=berlin)
    morning = int(datetime(2026, 11, 18, 9, 0, tzinfo=berlin).timestamp() * 1000)
    trades = [
        {"symbol": "BTC/USDT", "side": "buy", "price": 100.0, "amount": 1.0, "timestamp": morning},
        {"symbol": "BTC/USDT", "side": "sell", "price": 110.0, "amount": 1.0, "timestamp": morning + 60000, "fee": {"cost": 0.5, "currency": "USDT"}},
    ]

    result = calculate_daily_performance(trades, usdc_balance=1000.0, now=now)

    assert result["profit"] == 9.5
    assert result["loss"] == 0.0
    assert result["profit_percent"] == pytest.approx(9.5)


def test_daily_performance_excludes_previous_day_trades():
    berlin = ZoneInfo("Europe/Berlin")
    now = datetime(2026, 11, 18, 12, 0, tzinfo=berlin)
    yesterday = int(datetime(2026, 11, 17, 23, 0, tzinfo=berlin).timestamp() * 1000)
    result = calculate_daily_performance([
        {"symbol": "BTC/USDT", "side": "sell", "price": 110.0, "amount": 1.0, "timestamp": yesterday, "pnl": 50.0},
    ], usdc_balance=1000.0, now=now)

    assert result["profit"] == 0.0
    assert result["loss"] == 0.0


def test_risk_manager_persists_daily_stop_until_next_trading_day(tmp_path, monkeypatch):
    state_path = Path(tmp_path) / "risk_state.json"
    risk = RiskManager(RiskStateStore(state_path))
    now = datetime(2026, 11, 18, 12, 0, tzinfo=ZoneInfo("Europe/Berlin"))

    stopped = risk.evaluate(
        usdc_balance=100.0,
        profit=0.0,
        loss=0.0,
        performance_percent=0.0,
        profit_percent=0.0,
        loss_percent=4.0,
        now=now,
    )

    assert stopped["should_stop"] is True
    assert risk.state_store.load()["status"] == "STOPPED"

    state = risk.state_store.load()
    state["stop_until"] = "2026-11-17"
    state["status"] = "STOPPED"
    risk.state_store.save(state)
    resumed = risk.evaluate(
        usdc_balance=10.0,
        profit=0.0,
        loss=0.0,
        performance_percent=0.0,
        profit_percent=0.0,
        loss_percent=0.0,
        now=now,
    )
    assert resumed["should_stop"] is False
