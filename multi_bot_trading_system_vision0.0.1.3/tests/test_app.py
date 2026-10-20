import pytest

from backend import config
from backend.app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_dashboard_renders(client):
    response = client.get('/')

    assert response.status_code == 200
    assert b'Multi-Bot Trading System' in response.data
    assert b'/api/v1/' not in response.data
    assert b"fetch('/api/signals')" in response.data


def test_risk_limit_can_be_read_and_updated(client, monkeypatch):
    monkeypatch.setattr(config, 'MAX_DAILY_LOSS', 10.0)

    response = client.get('/api/risk/limit')
    assert response.status_code == 200
    assert response.get_json() == {'current_limit': 10.0}

    response = client.post('/api/risk/limit', json={'max_daily_loss_eur': 25})
    assert response.status_code == 200
    assert response.get_json() == {'success': True, 'current_limit': 25.0}
    assert config.MAX_DAILY_LOSS == 25.0


@pytest.mark.parametrize('payload', [{}, {'max_daily_loss_eur': 'invalid'}, {'max_daily_loss_eur': 0}])
def test_risk_limit_rejects_invalid_values(client, payload):
    response = client.post('/api/risk/limit', json=payload)

    assert response.status_code == 400
    assert 'error' in response.get_json()
