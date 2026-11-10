import ccxt
import pytest
from unittest.mock import patch

from backend.services.wallet_service import WalletService


@patch('backend.services.wallet_service.config.USE_TESTNET', True)
@patch('backend.services.wallet_service.config.BINANCE_API_KEY', 'test-key')
@patch('backend.services.wallet_service.config.BINANCE_SECRET_KEY', 'test-secret')
@patch('backend.services.wallet_service.ccxt.binance')
def test_wallet_initializes_exchange_and_values_assets(mock_binance):
    exchange = mock_binance.return_value
    exchange.fetch_balance.return_value = {
        'info': {},
        'BTC': {'free': 0.05, 'total': 0.1},
        'USDT': {'free': 500, 'total': 600},
    }
    exchange.fetch_ticker.return_value = {'last': 100000}

    wallet = WalletService().get_wallet_sync()

    assert mock_binance.call_args.args[0]['options']['adjustForTimeDifference'] is True
    exchange.set_sandbox_mode.assert_called_once_with(True)
    exchange.load_time_difference.assert_called_once_with()
    exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
    assert wallet['total_usdt'] == 10600
    assert wallet['balances'] == [
        {'asset': 'BTC', 'free': '0.05', 'locked': '0.05', 'usdt_value': 10000.0},
        {'asset': 'USDT', 'free': '500.0', 'locked': '100.0', 'usdt_value': 600.0},
    ]


@patch('backend.services.wallet_service.config.BINANCE_API_KEY', '')
@patch('backend.services.wallet_service.config.BINANCE_SECRET_KEY', '')
def test_wallet_reports_missing_credentials():
    with pytest.raises(ValueError, match='Binance API keys not configured'):
        WalletService().get_wallet_sync()


@patch('backend.services.wallet_service.config.USE_TESTNET', True)
@patch('backend.services.wallet_service.config.BINANCE_API_KEY', 'test-key')
@patch('backend.services.wallet_service.config.BINANCE_SECRET_KEY', 'test-secret')
@patch('backend.services.wallet_service.ccxt.binance')
def test_wallet_propagates_authentication_errors(mock_binance):
    exchange = mock_binance.return_value
    exchange.fetch_balance.side_effect = ccxt.AuthenticationError('invalid credentials')

    with pytest.raises(ccxt.AuthenticationError):
        WalletService().get_wallet_sync()
