import json

import pytest

from backend.services.analysis_service import (
    AnalysisRequestError,
    AnalysisService,
    RuleConfigurationError,
)


def _write_rules(path, actions, version=1):
    rules = {
        "version": version,
        "analysis_rules": [
            {
                "step": step,
                "action": action,
                "title": action.title(),
                "instructions": f"Follow {action}.",
            }
            for step, action in enumerate(actions, 1)
        ],
    }
    path.write_text(json.dumps(rules), encoding="utf-8")


def _service(tmp_path, actions, *, indicator_result=None, strategies=None):
    rules_path = tmp_path / "regeln.json"
    history_path = tmp_path / "history.jsonl"
    _write_rules(rules_path, actions)
    indicator = type(
        "IndicatorStub",
        (),
        {"get_indicators": lambda self, symbol, timeframe: indicator_result},
    )()
    calls = {"update": 0}

    def update_candles(symbol, timeframe):
        calls["update"] += 1
        return {"success": True}

    def load_candles(symbol, timeframe):
        return {"candles": [{"open": 1, "high": 2, "low": 0.5, "close": 1.5}] * 30}, True

    service = AnalysisService(
        indicator,
        strategy_service=strategies,
        rules_path=rules_path,
        history_path=history_path,
        candle_loader=load_candles,
        candle_updater=update_candles,
        news_collector=lambda: {"total_new": 0},
        news_item_loader=lambda: [],
    )
    return service, rules_path, history_path, calls


def test_analysis_loads_updated_rules_and_persists_each_run(tmp_path):
    indicators = {
        "rsi": [25],
        "macd": [1.0],
        "signal": [0.5],
        "hist": [0.5],
        "ema": [100.0],
        "symbol": "BTC/USDT",
        "timeframe": "1h",
    }
    service, rules_path, history_path, _ = _service(
        tmp_path, ["indicators"], indicator_result=indicators
    )

    first = service.analyze("BTC", "1h", [])
    _write_rules(rules_path, ["summary"], version=2)
    second = service.analyze("BTCUSDT", "1h", [])

    assert first["symbol"] == "BTCUSDT"
    assert first["summary"]["signal"] == "BUY"
    assert first["rules_version"] == 1
    assert second["rules_version"] == 2
    assert first["rules_sha256"] != second["rules_sha256"]
    assert [json.loads(line)["rules_version"] for line in history_path.read_text().splitlines()] == [1, 2]


def test_analysis_preserves_rule_order_and_continues_to_summary_on_failed_step(tmp_path):
    service, _, _, _ = _service(
        tmp_path, ["indicators", "summary"], indicator_result=None
    )

    result = service.analyze("BTC", "1h", [])

    assert [step["action"] for step in result["steps"]] == ["indicators", "summary"]
    assert result["steps"][0]["status"] == "failed"
    assert result["steps"][1]["status"] == "completed"
    assert result["status"] == "partial"
    assert result["failed_steps"] == [1]
    assert result["summary"]["incomplete_steps"] == [1]


def test_analysis_rejects_empty_strategy_selection_before_fetching_data(tmp_path):
    service, _, _, calls = _service(tmp_path, ["strategies"])

    with pytest.raises(AnalysisRequestError, match="mindestens eine Strategie"):
        service.analyze("BTC", "1h", [])

    assert calls["update"] == 0


def test_analysis_runs_only_the_selected_strategy(tmp_path):
    service, _, _, calls = _service(tmp_path, ["strategies"])

    result = service.analyze("BTC", "1h", ["trend"])

    assert calls["update"] == 1
    assert result["strategies"] == ["trend"]
    assert [item["strategy"] for item in result["steps"][0]["result"]["results"]] == [
        "trend"
    ]


def test_analysis_rejects_malformed_json_before_running_actions(tmp_path):
    service, rules_path, _, _ = _service(tmp_path, ["indicators"])
    rules_path.write_text("{", encoding="utf-8")

    with pytest.raises(RuleConfigurationError, match="JSON"):
        service.analyze("BTC", "1h", [])


@pytest.mark.parametrize(
    ("actions", "message"),
    [
        (["summary", "indicators"], "aufsteigende"),
        (["unknown"], "unterstützte Aktion"),
    ],
)
def test_analysis_rejects_invalid_rule_configuration(tmp_path, actions, message):
    service, rules_path, _, _ = _service(tmp_path, actions)
    if actions == ["summary", "indicators"]:
        payload = json.loads(rules_path.read_text(encoding="utf-8"))
        payload["analysis_rules"][0]["step"] = 2
        payload["analysis_rules"][1]["step"] = 1
        rules_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuleConfigurationError, match=message):
        service.analyze("BTC", "1h", [])


def test_analysis_rejects_unsupported_request_values(tmp_path):
    service, _, _, _ = _service(tmp_path, ["summary"])

    with pytest.raises(AnalysisRequestError, match="wird nicht unterstützt"):
        service.analyze("NOTACOIN", "1h", [])
    with pytest.raises(AnalysisRequestError, match="timeframe"):
        service.analyze("BTC", "2h", [])
    with pytest.raises(AnalysisRequestError, match="nicht mehrfach"):
        service.analyze("BTC", "1h", ["trend", "trend"])
