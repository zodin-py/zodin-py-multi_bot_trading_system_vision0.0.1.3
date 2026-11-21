"""HTTP endpoints for Spot trade execution."""

from flask import Blueprint, jsonify, request

from backend.services.trade_execution_service import (
    TradeExecutionError,
    TradeExecutionService,
)

trade_api = Blueprint("trade_api", __name__)


@trade_api.route("/api/trade/execute", methods=["POST"])
def execute_trade():
    """Execute a protected Spot trade.

    Example JSON body:
    {
        "symbol": "BTCUSDT",
        "entry_price": 95000.0,
        "amount": 100.0,
        "take_profit": 97000.0,
        "stop_loss": 94000.0,
        "sl_limit": 93800.0
    }

    ``amount`` is the amount to spend in the configured quote currency.
    ``sl_limit`` is optional; when omitted, the stop-loss leg is a market stop.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "status": "ERROR",
            "error_code": "INVALID_JSON",
            "message": "Valid JSON request body is required",
        }), 400

    try:
        return jsonify(TradeExecutionService().execute(data)), 200
    except TradeExecutionError as error:
        return jsonify(error.to_dict()), error.http_status
