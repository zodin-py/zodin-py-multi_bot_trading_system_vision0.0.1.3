import json
from unittest.mock import patch


def _api_only_module():
    with patch('backend.services.price_service.PriceService.start'):
        from backend import api_only
    return api_only


def test_api_only_coins_route_matches_frontend_response():
    api_only = _api_only_module()

    response = api_only.app.test_client().get('/api/coins')

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'BTCUSDT' in data['coins']
    assert '5m' in data['timeframes']


def test_api_only_select_route_fetches_and_persists_candles(monkeypatch):
    api_only = _api_only_module()
    summary = {
        'success': True,
        'candles_loaded': 500,
        'new_candles': 500,
        'duplicates_skipped': 0,
    }
    update = lambda symbol, timeframe: summary
    monkeypatch.setattr(api_only, 'update_candle_data', update)

    response = api_only.app.test_client().post(
        '/api/coins/BTCUSDT/select',
        json={'timeframe': '1h'},
    )

    assert response.status_code == 200
    assert response.get_json()['candles_loaded'] == 500


def test_api_only_candles_route_returns_latest_requested_candles(monkeypatch):
    api_only = _api_only_module()
    candles = [{'open_time': timestamp} for timestamp in range(5)]
    monkeypatch.setattr(
        api_only,
        'load_candles',
        lambda symbol, timeframe: ({'candles': candles}, True),
    )

    response = api_only.app.test_client().get(
        '/api/coins/BTCUSDT/candles?timeframe=5m&limit=2',
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['candles'] == candles[-2:]
    assert data['candle_count'] == 5
    assert data['returned_count'] == 2


def test_api_only_trades_route_reads_history_and_applies_limit(monkeypatch, tmp_path):
    api_only = _api_only_module()
    history = [
        {'id': 'TRD00001'},
        {'id': 'TRD00002'},
        {'id': 'TRD00003'},
    ]
    history_path = tmp_path / 'trades_history.json'
    history_path.write_text(json.dumps(history), encoding='utf-8')
    monkeypatch.setattr(api_only, 'TRADES_HISTORY_FILE', str(history_path))

    response = api_only.app.test_client().get('/api/trades?limit=2')

    assert response.status_code == 200
    assert response.get_json() == history[-2:]


def test_api_only_trades_route_rejects_invalid_limit():
    api_only = _api_only_module()

    response = api_only.app.test_client().get('/api/trades?limit=0')

    assert response.status_code == 400
    assert response.get_json()['error'] == 'limit must be a positive integer'


def test_api_only_root_serves_built_angular_dashboard(monkeypatch, tmp_path):
    api_only = _api_only_module()
    (tmp_path / 'index.html').write_text('<html>dashboard</html>', encoding='utf-8')
    monkeypatch.setattr(api_only, 'ANGULAR_DIST', str(tmp_path))

    response = api_only.app.test_client().get('/')

    assert response.status_code == 200
    assert response.get_data(as_text=True) == '<html>dashboard</html>'


def test_api_only_wallet_route_returns_authentication_error(monkeypatch):
    from ccxt.base.errors import AuthenticationError

    from backend.services.wallet_service import WalletService

    api_only = _api_only_module()

    def reject_credentials(self):
        raise AuthenticationError('private exchange details')

    monkeypatch.setattr(WalletService, 'get_wallet_sync', reject_credentials)

    response = api_only.app.test_client().get('/api/wallet')

    assert response.status_code == 401
    assert response.get_json() == {
        'error': 'Binance API key, IP allow-list, or permissions are invalid',
        'data': None,
    }


def test_api_only_analysis_route_passes_request_to_service(monkeypatch):
    api_only = _api_only_module()
    request_data = {}

    def analyze(symbol, timeframe, strategies):
        request_data.update(
            symbol=symbol,
            timeframe=timeframe,
            strategies=strategies,
        )
        return {'status': 'completed', 'summary': {'signal': 'HOLD'}}

    monkeypatch.setattr(api_only.analysis_service, 'analyze', analyze)

    response = api_only.app.test_client().post(
        '/api/analyze',
        json={'symbol': 'BTC', 'timeframe': '1h', 'strategies': ['trend']},
    )

    assert response.status_code == 200
    assert request_data == {
        'symbol': 'BTC',
        'timeframe': '1h',
        'strategies': ['trend'],
    }
    assert response.get_json()['summary']['signal'] == 'HOLD'


def test_api_only_analysis_route_rejects_missing_request_fields():
    api_only = _api_only_module()

    response = api_only.app.test_client().post('/api/analyze', json={})

    assert response.status_code == 400
    assert 'symbol' in response.get_json()['error']
