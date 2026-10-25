import pytest
from unittest.mock import MagicMock

import backend.app as dashboard

from backend import config
from backend.app import app


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_dashboard_serves_angular_build(client, tmp_path, monkeypatch):
    build_dir = tmp_path / 'browser'
    build_dir.mkdir()
    (build_dir / 'index.html').write_text(
        '<!doctype html><app-root></app-root>',
        encoding='utf-8',
    )
    monkeypatch.setattr(dashboard, 'angular_dist', str(build_dir))

    response = client.get('/')
    spa_response = client.get('/dashboard')

    assert response.status_code == 200
    assert b'<app-root></app-root>' in response.data
    assert spa_response.status_code == 200
    assert spa_response.data == response.data


def test_dashboard_requires_angular_build(client, tmp_path, monkeypatch):
    monkeypatch.setattr(dashboard, 'angular_dist', str(tmp_path / 'missing'))

    response = client.get('/')

    assert response.status_code == 503
    assert 'Angular build not found' in response.get_json()['error']


def test_unknown_api_route_is_not_handled_by_spa(client, tmp_path, monkeypatch):
    build_dir = tmp_path / 'browser'
    build_dir.mkdir()
    (build_dir / 'index.html').write_text('<app-root></app-root>', encoding='utf-8')
    monkeypatch.setattr(dashboard, 'angular_dist', str(build_dir))

    response = client.get('/api/unknown')

    assert response.status_code == 404


def test_portfolio_returns_binance_balance(client, monkeypatch):
    fake_executor = MagicMock()
    fake_executor.get_portfolio.return_value = {'capital': 1234.56}
    monkeypatch.setattr(dashboard, 'executor', fake_executor)

    response = client.get('/api/portfolio')

    assert response.status_code == 200
    assert response.get_json()['capital'] == 1234.56


def test_portfolio_does_not_return_paper_capital_on_binance_error(client, monkeypatch):
    fake_executor = MagicMock()
    fake_executor.get_portfolio.side_effect = RuntimeError('Binance balance unavailable')
    monkeypatch.setattr(dashboard, 'executor', fake_executor)

    response = client.get('/api/portfolio')

    assert response.status_code == 502
    assert response.get_json() == {'error': 'Binance balance unavailable'}


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
