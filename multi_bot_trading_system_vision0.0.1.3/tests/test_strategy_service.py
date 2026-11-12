from backend.services.strategy_service import StrategyAnalysisService


def _candle(open_price, high, low, close):
    return {"open": open_price, "high": high, "low": low, "close": close}


def test_trend_strategy_detects_confirmed_rising_ema_alignment():
    candles = [
        _candle(100 + index, 101 + index, 99 + index, 100 + index)
        for index in range(50)
    ]

    result = StrategyAnalysisService().analyze(["trend"], candles)[0]

    assert result["status"] == "completed"
    assert result["signal"] == "BUY"
    assert result["data"]["ema_9"] > result["data"]["ema_21"]


def test_smc_strategy_reports_price_inside_bullish_fair_value_gap():
    candles = [
        _candle(9, 10, 8, 9.5),
        _candle(10.5, 12, 10, 11.5),
        _candle(12, 13, 11, 12),
        _candle(10.4, 10.8, 10.2, 10.5),
    ]

    result = StrategyAnalysisService().analyze(["smc"], candles)[0]

    assert result["signal"] == "BUY"
    assert result["data"]["fair_value_gap"]["direction"] == "bullish"


def test_support_resistance_strategy_signals_near_confirmed_support():
    candles = [_candle(100, 100.2, 99.8, 100) for _ in range(30)]
    candles[10] = _candle(99.5, 100, 99.5, 99.7)

    result = StrategyAnalysisService().analyze(["sr"], candles)[0]

    assert result["signal"] == "BUY"
    assert result["data"]["nearest_support"] == 99.5


def test_harmonic_strategy_recognizes_a_bullish_gartley_ratio_sequence():
    candles = [_candle(130, 131, 129, 130) for _ in range(27)]
    candles[3] = _candle(100.5, 101, 100, 100.5)
    candles[8] = _candle(149.5, 150, 149, 149.5)
    candles[13] = _candle(119.5, 120, 119, 119.5)
    candles[18] = _candle(136.5, 137, 136, 136.5)
    candles[23] = _candle(111, 111.7, 110.7, 111)

    result = StrategyAnalysisService().analyze(["harmonic"], candles)[0]

    assert result["signal"] == "BUY"
    assert result["data"]["pattern"] == "Gartley"


def test_harmonic_strategy_marks_insufficient_swings_inconclusive():
    result = StrategyAnalysisService().analyze(
        ["harmonic"], [_candle(1, 2, 0.5, 1.5)] * 4
    )[0]

    assert result["status"] == "inconclusive"
    assert result["signal"] == "INCONCLUSIVE"
