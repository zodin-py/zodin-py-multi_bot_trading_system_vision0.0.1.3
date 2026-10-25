"""Tests for indicators service."""
import pytest
from unittest.mock import MagicMock, patch

from backend.services.indicators_service import IndicatorService


class TestIndicatorsService:
    """Tests for IndicatorService."""

    @patch('backend.services.indicators_service.ccxt.binance')
    def test_get_indicators_returns_20_values(self, mock_binance):
        """Verify indicators service returns exactly 20 values for RSI, MACD, EMA."""
        # Setup mock exchange
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange

        # Create mock OHLCV data (50 candles)
        mock_candles = []
        base_price = 80000.0
        for i in range(50):
            mock_candles.append([
                1000000 + i * 3600000,  # timestamp
                base_price + i * 10,    # open
                base_price + i * 10 + 50,  # high
                base_price + i * 10 - 50,  # low
                base_price + i * 10,    # close
                100.0                   # volume
            ])

        mock_exchange.fetch_ohlcv.return_value = mock_candles

        # Create service and call
        service = IndicatorService()
        result = service.get_indicators('btc', '1h')

        # Verify result structure
        assert result is not None
        assert 'rsi' in result
        assert 'macd' in result
        assert 'signal' in result
        assert 'hist' in result
        assert 'ema' in result
        assert 'timeframe' in result
        assert 'symbol' in result

        # Verify exactly 20 values each
        assert len(result['rsi']) == 20, f"Expected 20 RSI values, got {len(result['rsi'])}"
        assert len(result['macd']) == 20, f"Expected 20 MACD values, got {len(result['macd'])}"
        assert len(result['signal']) == 20, f"Expected 20 signal values, got {len(result['signal'])}"
        assert len(result['hist']) == 20, f"Expected 20 hist values, got {len(result['hist'])}"
        assert len(result['ema']) == 20, f"Expected 20 EMA values, got {len(result['ema'])}"

        # Verify symbol format
        assert result['symbol'] == 'BTC/USDT'
        assert result['timeframe'] == '1h'

    @patch('backend.services.indicators_service.ccxt.binance')
    def test_get_indicators_invalid_coin(self, mock_binance):
        """Verify error handling for invalid coin."""
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange
        mock_exchange.fetch_ohlcv.side_effect = Exception("Symbol not found")

        service = IndicatorService()
        result = service.get_indicators('invalidcoin999', '1h')

        assert result is None

    @patch('backend.services.indicators_service.ccxt.binance')
    def test_get_indicators_insufficient_data(self, mock_binance):
        """Verify handling of insufficient candle data."""
        mock_exchange = MagicMock()
        mock_binance.return_value = mock_exchange

        # Return only 5 candles (insufficient for 20 indicator values)
        mock_exchange.fetch_ohlcv.return_value = [
            [1000000 + i * 3600000, 80000, 80100, 79900, 80000, 100.0]
            for i in range(5)
        ]

        service = IndicatorService()
        result = service.get_indicators('btc', '1h')

        assert result is None

    def test_normalize_coin(self):
        """Test coin normalization."""
        assert IndicatorService._normalize_coin('btc') == 'BTCUSDT'
        assert IndicatorService._normalize_coin('BTC') == 'BTCUSDT'
        assert IndicatorService._normalize_coin('btcusdt') == 'BTCUSDT'
        assert IndicatorService._normalize_coin('BTCUSDT') == 'BTCUSDT'

    def test_format_symbol_for_response(self):
        """Test symbol formatting for response."""
        assert IndicatorService._format_symbol_for_response('BTCUSDT') == 'BTC/USDT'
        assert IndicatorService._format_symbol_for_response('ETHUSDT') == 'ETH/USDT'
        # Already formatted - should remain unchanged
        assert IndicatorService._format_symbol_for_response('BTC/USDT') == 'BTC/USDT'

    def test_normalize_timeframe(self):
        """Test timeframe normalization."""
        assert IndicatorService._normalize_timeframe('1h') == '1h'
        assert IndicatorService._normalize_timeframe('4h') == '4h'
        assert IndicatorService._normalize_timeframe('1d') == '1d'
        assert IndicatorService._normalize_timeframe('invalid') == '1h'  # default