"""Tests for price service (WebSocket-based)."""
import pytest
from unittest.mock import MagicMock, patch
import time

from backend.services.price_service import PriceService


class TestPriceService:
    """Tests for PriceService WebSocket implementation."""

    def test_normalize_symbol(self):
        """Test symbol normalization - ensures proper USDT suffix and slash."""
        # All formats should normalize to BTC/USDT format (with slash)
        assert PriceService._normalize_symbol('btc') == 'BTC/USDT'
        assert PriceService._normalize_symbol('BTC') == 'BTC/USDT'
        # Already has USDT suffix - add slash
        assert PriceService._normalize_symbol('btcusdt') == 'BTC/USDT'
        assert PriceService._normalize_symbol('BTCUSDT') == 'BTC/USDT'
        assert PriceService._normalize_symbol('BTC/USDT') == 'BTC/USDT'

    @patch('backend.services.price_service.PriceService._fetch_price_rest')
    def test_get_price_sync_uses_cache(self, mock_rest):
        """Test that cached prices are returned instantly."""
        mock_rest.return_value = {'symbol': 'BTC/USDT', 'price': 80000.0, 'timestamp': '2024-01-01T00:00:00+00:00'}

        # Populate cache
        with patch.object(PriceService, '_prices', {'BTC/USDT': {'symbol': 'BTC/USDT', 'price': 80000.0}}):
            with patch.object(PriceService, '_last_update', time.time()):
                result = PriceService.get_price_sync('btc')
                assert result['price'] == 80000.0
                assert 'error' not in result

    def test_fetch_price_rest(self):
        """Test REST fallback price fetch."""
        import ccxt
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = MagicMock()
            mock_binance.return_value = mock_exchange
            mock_exchange.fetch_ticker.return_value = {
                'symbol': 'BTC/USDT',
                'last': 80690.0,
                'timestamp': 1792943332943,
            }

            result = PriceService._fetch_price_rest('BTC/USDT')
            assert result['symbol'] == 'BTC/USDT'
            assert result['price'] == 80690.0

    def test_fetch_price_rest_error(self):
        """Test REST fallback error handling."""
        import ccxt
        with patch.object(ccxt, 'binance') as mock_binance:
            mock_exchange = MagicMock()
            mock_binance.return_value = mock_exchange
            mock_exchange.fetch_ticker.side_effect = Exception("Network error")

            result = PriceService._fetch_price_rest('BTC/USDT')
            assert 'error' in result
