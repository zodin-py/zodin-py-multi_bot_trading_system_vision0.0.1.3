from backend.candles import manager


def _candle(open_time: int, close_time: int) -> dict[str, int]:
    return {"open_time": open_time, "close_time": close_time}


def test_incremental_update_only_persists_closed_candles(monkeypatch):
    existing = [_candle(0, 999)]
    fetched = [_candle(1000, 1999), _candle(2000, 2999)]
    merged_input = []
    saved_candles = []

    monkeypatch.setattr(
        manager,
        "load_candles",
        lambda symbol, timeframe: ({"candles": existing}, True),
    )
    monkeypatch.setattr(
        manager,
        "fetch_historical_candles",
        lambda symbol, timeframe, limit, server_time: (fetched, None),
    )

    def capture_merge(old_candles, new_candles):
        merged_input.extend(new_candles)
        return old_candles + new_candles

    monkeypatch.setattr(manager, "merge_candles", capture_merge)
    monkeypatch.setattr(
        manager,
        "save_candles",
        lambda symbol, timeframe, candles: saved_candles.extend(candles) or True,
    )

    result = manager.update_candle_data("BTCUSDT", "5m", server_time=2500)

    assert result["success"] is True
    assert result["new_candles"] == 1
    assert merged_input == [fetched[0]]
    assert saved_candles == existing + [fetched[0]]
