"""Tests for WalletService API endpoint — integration tests via Flask test client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client():
    """Flask test client from existing test patterns."""
    from backend.app import app

    app.config.update(TESTING=True)
    return app.test_client()


class TestWalletServiceRoute:
    """Integration tests for /api/wallet endpoint."""

    def test_api_wallet_returns_200_with_structure(self, client, monkeypatch):
        """Test that /api/wallet returns 200 with correct structure."""
        from backend.services.wallet_service import WalletService

        # Create fake WalletService data
        fake_wallet = {
            'balances': [
                {'asset': 'BTC', 'free': '0.5', 'locked': '0.0', 'usdt_value': 33716.25},
                {'asset': 'USDT', 'free': '1000.00', 'locked': '0.0', 'usdt_value': 1000.00},
            ],
            'total_usdt': 34716.25,
            'timestamp': '2026-10-25T10:30:00Z',
        }

        # Monkey-patch the class method directly
        WalletService.get_wallet_sync = MagicMock(return_value=fake_wallet)

        response = client.get('/api/wallet')
        assert response.status_code == 200

        data = response.get_json()
        assert 'balances' in data
        assert 'total_usdt' in data
        assert 'timestamp' in data
        # Check first balance has expected keys
        assert len(data['balances']) >= 1
        assert 'asset' in data['balances'][0]
        assert 'usdt_value' in data['balances'][0]

    def test_api_wallet_empty_balances(self, client, monkeypatch):
        """Test /api/wallet with no balances."""
        from backend.services.wallet_service import WalletService

        WalletService.get_wallet_sync = MagicMock(return_value={
            'balances': [],
            'total_usdt': 0.0,
            'timestamp': '2026-10-25T10:30:00Z',
        })

        response = client.get('/api/wallet')
        assert response.status_code == 200

        data = response.get_json()
        assert data['balances'] == []
        assert data['total_usdt'] == 0.0

    def test_api_wallet_error_handling(self, client, monkeypatch):
        """Test /api/wallet handles WalletService error."""
        from backend.services.wallet_service import WalletService

        WalletService.get_wallet_sync = MagicMock(return_value={
            'error': 'Wallet unavailable',
            'data': None,
        })

        response = client.get('/api/wallet')
        # Service error returns 500 or graceful handling
        assert response.status_code in (200, 500)