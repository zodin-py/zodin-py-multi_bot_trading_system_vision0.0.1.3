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
