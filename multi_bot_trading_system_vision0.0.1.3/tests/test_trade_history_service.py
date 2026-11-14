from unittest.mock import Mock

from backend.services.trade_history_service import TradeHistoryService


def test_trade_history_fetches_live_spot_fills_for_configured_pairs(monkeypatch):
    from backend.services import trade_history_service

    exchange = Mock()
    exchange.fetch_my_trades.side_effect = [
        [
            {
                'id': 'btc-1',
                'symbol': 'BTC/USDT',
                'side': 'buy',
                'price': 100,
                'amount': 0.5,
                'cost': 50,
                'timestamp': 1_700_000_000_000,
                'datetime': '2023-11-14T22:13:20.000Z',
                'order': 'order-1',
                'fee': {'cost': 0.001, 'currency': 'BTC'},
            },
        ],
        [
            {
                'id': 'eth-1',
                'symbol': 'ETH/USDT',
                'side': 'sell',
                'price': 200,
                'amount': 1,
                'cost': 200,
                'timestamp': 1_700_000_100_000,
                'datetime': '2023-11-14T22:15:00.000Z',
                'order': 'order-2',
                'fee': None,
            },
        ],
    ]
    wallet_service = Mock()
    wallet_service.exchange = exchange
    monkeypatch.setattr(
        trade_history_service,
        'WalletService',
        Mock(return_value=wallet_service),
    )
    monkeypatch.setattr(trade_history_service.config, 'BINANCE_API_KEY', 'configured')
    monkeypatch.setattr(trade_history_service.config, 'BINANCE_SECRET_KEY', 'configured')
    monkeypatch.setattr(trade_history_service.config, 'DEFAULT_QUOTE', 'USDT')
    monkeypatch.setattr(
        trade_history_service.config,
        'COINS',
        ['BTCUSDT', 'ETHUSDT'],
    )

    trades = TradeHistoryService().get_trade_history_sync(limit=1)

    exchange.set_sandbox_mode.assert_called_once_with(False)
    exchange.load_time_difference.assert_called_once_with()
    assert exchange.fetch_my_trades.call_args_list[0].args == ('BTC/USDT',)
    assert exchange.fetch_my_trades.call_args_list[0].kwargs == {'limit': 1}
    assert exchange.fetch_my_trades.call_args_list[1].args == ('ETH/USDT',)
    assert len(trades) == 1
    assert trades[0]['id'] == 'ETH/USDT:eth-1'
    assert trades[0]['side'] == 'sell'
    assert trades[0]['cost'] == 200


def test_trade_history_requires_credentials(monkeypatch):
    from backend.services import trade_history_service

    monkeypatch.setattr(trade_history_service.config, 'BINANCE_API_KEY', '')
    monkeypatch.setattr(trade_history_service.config, 'BINANCE_SECRET_KEY', '')

    try:
        TradeHistoryService().get_trade_history_sync()
    except ValueError as error:
        assert 'TRADING_BINANCE_API_KEY' in str(error)
    else:
        raise AssertionError('Expected missing Binance credentials to be reported')
