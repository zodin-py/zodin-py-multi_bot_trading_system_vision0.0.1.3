"""Tests for price service."""
import pytest
from unittest.mock import MagicMock, patch

from backend.services.price_service import PriceService, get_price_service


class TestPriceService:
    """Tests for PriceService."""

    @patch('backend.services.price_service.ccxt.binance')
    def test_price_service_valid_coin(self, mock_binance):
        """Test price service returns correct structure for valid coin."""
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange

        # Mock ticker response
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 80690.0,
            'timestamp': 1792943332943,
        }

        service = PriceService()
        result = service.get_price_sync('btc')

        assert result['symbol'] == 'BTC/USDT'
        assert result['price'] == 80690.0
        assert 'timestamp' in result
        assert 'error' not in result

    @patch('backend.services.price_service.ccxt.binance')
    def test_price_service_appends_usdt(self, mock_binance):
        """Test that coin input without USDT gets /USDT appended."""
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 80690.0,
            'timestamp': 1792943332943,
        }

        service = PriceService()
        result = service.get_price_sync('btc')

        # Verify ccxt was called with BTC/USDT
        mock_exchange.fetch_ticker.assert_called_once_with('BTC/USDT')
        assert result['symbol'] == 'BTC/USDT'

    @patch('backend.services.price_service.ccxt.binance')
    def test_price_service_invalid_coin(self, mock_binance):
        """Test error response for invalid coin."""
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange
        mock_exchange.fetch_ticker.side_effect = Exception("Symbol not found")

        service = PriceService()
        result = service.get_price_sync('invalidcoin999')

        assert result['error'] == 'Coin not found'
        assert result['data'] is None

    @patch('backend.services.price_service.ccxt.binance')
    def test_price_service_with_usdt_suffix(self, mock_binance):
        """Test coin input that already has USDT suffix."""
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange
        mock_exchange.fetch_ticker.return_value = {
            'symbol': 'BTC/USDT',
            'last': 80690.0,
            'timestamp': 1792943332943,
        }

        service = PriceService()
        result = service.get_price_sync('BTCUSDT')

        # Input BTCUSDT should be normalized to BTC/USDT
        assert result['symbol'] == 'BTC/USDT'
        assert result['price'] == 80690.0

    def test_normalize_symbol(self):
        """Test symbol normalization."""
        assert PriceService._normalize_symbol('btc') == 'BTC/USDT'
        assert PriceService._normalize_symbol('BTC') == 'BTC/USDT'
        assert PriceService._normalize_symbol('btcusdt') == 'BTC/USDT'  # Already has USDT suffix
        assert PriceService._normalize_symbol('BTCUSDT') == 'BTC/USDT'  # Already has USDT suffix