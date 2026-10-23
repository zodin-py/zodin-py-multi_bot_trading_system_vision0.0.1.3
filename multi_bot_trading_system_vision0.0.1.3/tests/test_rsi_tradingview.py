from backend.bots.base_bot import SignalType
from backend.indicators.provider import MockIndicatorProvider, _IndicatorFixture
from backend.indicators.rsi_bot import RSIBot


def test_rsi_bot_generates_oversold_signal():
    provider = MockIndicatorProvider()
    provider.set_indicators('BTCUSDT', '1h', _IndicatorFixture(rsi=28.0))

    signal = RSIBot().analyze('BTCUSDT', '1h', provider)

    assert signal.signal_type is SignalType.BUY
    assert signal.details['rsi'] == 28.0
    assert signal.details['zone'] == 'oversold'
