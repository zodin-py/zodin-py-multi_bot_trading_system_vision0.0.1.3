import pytest
from backend.api import trade_endpoints
from backend.services import trade_execution_service
from backend.services.trade_execution_service import (
    TradeExecutionError,
    TradeExecutionService,
)


class FakeExchange:
    has = {"createMarketBuyOrderWithCost": True}

    def __init__(self):
        self.oco_params = None
        self.buy_amount = None

    def load_markets(self):
        return {"BTC/USDT": {"id": "BTCUSDT"}}

    def create_market_buy_order_with_cost(self, symbol, cost):
        self.buy_amount = (symbol, cost)
        return {
            "id": "entry-1",
            "status": "closed",
            "filled": 0.001,
            "average": 95000,
        }

    def amount_to_precision(self, symbol, amount):
        assert symbol == "BTC/USDT"
        return f"{float(amount):.8f}".rstrip("0").rstrip(".")

    def price_to_precision(self, symbol, price):
        assert symbol == "BTC/USDT"
        return f"{float(price):.2f}"

    def private_post_orderlist_oco(self, params):
        self.oco_params = params
        return {
            "orderListId": 123,
            "orderReports": [
                {"type": "LIMIT_MAKER", "orderId": 456},
                {"type": "STOP_LOSS_LIMIT", "orderId": 789},
            ],
        }


class FakeWalletService:
    def __init__(self, exchange, free_balance="500"):
        self.exchange = exchange
        self.free_balance = free_balance

    def get_wallet_sync(self):
        return {
            "balances": [
                {"asset": "USDT", "free": self.free_balance, "locked": "100"}
            ]
        }


@pytest.fixture
def configured_trade_service(monkeypatch):
    exchange = FakeExchange()
    wallet_service = FakeWalletService(exchange)
    monkeypatch.setattr(trade_execution_service, "WalletService", lambda: wallet_service)
    monkeypatch.setattr(trade_execution_service.config, "BINANCE_API_KEY", "test-key")
    monkeypatch.setattr(trade_execution_service.config, "BINANCE_SECRET_KEY", "test-secret")
    monkeypatch.setattr(
        trade_execution_service.PriceService,
        "get_price_sync",
        lambda symbol: {"price": 95000, "symbol": symbol},
    )
    return TradeExecutionService(), exchange, wallet_service


def _request(**overrides):
    data = {
        "symbol": "BTCUSDT",
        "entry_price": 95000,
        "amount": 100,
        "take_profit": 97000,
        "stop_loss": 94000,
        "sl_limit": 93800,
    }
    data.update(overrides)
    return data


def test_trade_service_places_quote_buy_and_binance_oco(configured_trade_service):
    service, exchange, _ = configured_trade_service

    result = service.execute(_request())

    assert result["status"] == "SUCCESS"
    assert exchange.buy_amount == ("BTC/USDT", 100.0)
    assert exchange.oco_params == {
        "symbol": "BTCUSDT",
        "side": "SELL",
        "quantity": "0.001",
        "aboveType": "LIMIT_MAKER",
        "abovePrice": "97000.00",
        "belowType": "STOP_LOSS_LIMIT",
        "belowStopPrice": "94000.00",
        "belowPrice": "93800.00",
        "belowTimeInForce": "GTC",
    }
    assert result["binance_order_ids"] == {
        "entry_order": "entry-1",
        "oco_order": 123,
        "take_profit_order": 456,
        "stop_loss_order": 789,
    }


def test_trade_service_rejects_spending_locked_quote_balance(configured_trade_service):
    service, exchange, wallet_service = configured_trade_service
    wallet_service.free_balance = "50"

    with pytest.raises(TradeExecutionError) as error:
        service.execute(_request(amount=100))

    assert error.value.error_code == "INSUFFICIENT_BALANCE"
    assert exchange.buy_amount is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entry_price", float("nan")),
        ("amount", 0),
        ("take_profit", 94000),
        ("stop_loss", 95000),
        ("sl_limit", 94000),
    ],
)
def test_trade_service_rejects_invalid_values_before_exchange(field, value):
    with pytest.raises(TradeExecutionError):
        TradeExecutionService._validate_request(_request(**{field: value}))


def test_trade_execute_endpoint_returns_validation_errors_as_json():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(trade_endpoints.trade_api)

    response = app.test_client().post("/api/trade/execute", json={"symbol": "BTCUSDT"})

    assert response.status_code == 400
    assert response.get_json()["error_code"] == "INVALID_FIELD"
