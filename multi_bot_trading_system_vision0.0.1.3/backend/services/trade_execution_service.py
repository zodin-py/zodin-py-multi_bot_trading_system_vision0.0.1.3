"""Validated Binance Spot trade execution with OCO exit protection."""

from __future__ import annotations

import logging
import math
from typing import Any, NoReturn

import ccxt

from backend import config
from backend.services.price_service import PriceService
from backend.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class TradeExecutionError(Exception):
    """An expected trade failure that can be returned by the HTTP API."""

    def __init__(
        self,
        error_code: str,
        message: str,
        http_status: int = 400,
        *,
        status: str = "ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.http_status = http_status
        self.status = status
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "error_code": self.error_code,
            "message": self.message,
            **self.details,
        }


class TradeExecutionService:
    """Validates and executes a market buy followed by a Binance OCO sell."""

    def __init__(self, wallet_service: WalletService | None = None) -> None:
        self.wallet_service = wallet_service or WalletService()

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        symbol, exchange_symbol, entry_price, quote_amount, take_profit, stop_loss, sl_limit = (
            self._validate_request(data)
        )

        if not config.BINANCE_API_KEY or not config.BINANCE_SECRET_KEY:
            raise TradeExecutionError(
                "INVALID_API_CONFIG",
                "Binance API keys are not configured",
                401,
            )

        exchange = self.wallet_service.exchange
        try:
            markets = exchange.load_markets()
        except ccxt.BaseError as error:
            logger.error("Could not load Binance markets: %s", type(error).__name__)
            raise TradeExecutionError(
                "BINANCE_API_ERROR", "Could not load Binance markets", 502
            ) from error

        market = markets.get(symbol)
        if market is None:
            raise TradeExecutionError(
                "INVALID_SYMBOL",
                f"Trading pair {symbol} is not available on Binance Spot",
            )
        exchange_symbol = str(market.get("id") or exchange_symbol)

        current_price_data = PriceService.get_price_sync(symbol)
        current_price = self._positive_number(
            current_price_data.get("price") if isinstance(current_price_data, dict) else None,
            "current market price",
            "MARKET_PRICE_UNAVAILABLE",
            503,
        )
        max_deviation = float(
            getattr(config.config, "MAX_ENTRY_PRICE_DEVIATION_PERCENT", 0.5)
        )
        deviation_percent = abs(current_price - entry_price) / entry_price * 100
        if deviation_percent > max_deviation:
            raise TradeExecutionError(
                "ENTRY_PRICE_DEVIATION",
                "Entry price is too far from the current market price",
                400,
                details={
                    "current_market_price": current_price,
                    "deviation_percent": round(deviation_percent, 3),
                    "max_deviation_percent": max_deviation,
                },
            )

        wallet = self.wallet_service.get_wallet_sync()
        if not isinstance(wallet, dict) or wallet.get("error"):
            raise TradeExecutionError(
                "WALLET_UNAVAILABLE", "Could not fetch wallet balance", 502
            )

        quote_currency = config.DEFAULT_QUOTE.upper()
        quote_balance = self._free_balance(wallet, quote_currency)
        if quote_amount > quote_balance:
            raise TradeExecutionError(
                "INSUFFICIENT_BALANCE",
                f"Requested amount exceeds the available {quote_currency} balance",
                400,
                details={
                    "requested_amount": quote_amount,
                    "available_balance": quote_balance,
                    "asset": quote_currency,
                },
            )

        try:
            if not exchange.has.get("createMarketBuyOrderWithCost"):
                raise TradeExecutionError(
                    "UNSUPPORTED_MARKET_BUY",
                    "The configured Binance client does not support quote-cost market buys",
                    503,
                )
            order = exchange.create_market_buy_order_with_cost(symbol, quote_amount)
        except TradeExecutionError:
            raise
        except ccxt.BaseError as error:
            logger.error("Binance market buy failed: %s", type(error).__name__)
            raise TradeExecutionError(
                "BINANCE_API_ERROR", "Binance rejected the market buy order", 502
            ) from error

        if not isinstance(order, dict):
            raise TradeExecutionError(
                "ORDER_FILL_UNKNOWN",
                "Binance returned an invalid market order response; verify the order before retrying",
                502,
            )

        filled = order.get("filled")
        if filled is None and order.get("status") == "closed":
            filled = order.get("amount")
        try:
            filled_quantity = float(exchange.amount_to_precision(symbol, filled))
        except (TypeError, ValueError, ccxt.BaseError) as error:
            logger.error("Could not determine filled trade quantity: %s", type(error).__name__)
            raise TradeExecutionError(
                "ORDER_FILL_UNKNOWN",
                "Could not determine the filled quantity; verify the order before retrying",
                502,
                details={"entry_order_id": order.get("id")},
            ) from error

        if not math.isfinite(filled_quantity) or filled_quantity <= 0:
            raise TradeExecutionError(
                "ORDER_FILL_UNKNOWN",
                "Binance did not report a filled quantity; verify the order before retrying",
                502,
                details={"entry_order_id": order.get("id")},
            )

        try:
            take_profit_price = exchange.price_to_precision(symbol, take_profit)
            stop_loss_price = exchange.price_to_precision(symbol, stop_loss)
            oco_params: dict[str, Any] = {
                "symbol": exchange_symbol,
                "side": "SELL",
                "quantity": str(filled_quantity),
                "aboveType": "LIMIT_MAKER",
                "abovePrice": take_profit_price,
                "belowType": "STOP_LOSS_LIMIT" if sl_limit is not None else "STOP_LOSS",
                "belowStopPrice": stop_loss_price,
            }
            if sl_limit is not None:
                oco_params["belowPrice"] = exchange.price_to_precision(symbol, sl_limit)
                oco_params["belowTimeInForce"] = "GTC"

            create_oco = getattr(exchange, "private_post_orderlist_oco", None)
            if create_oco is None:
                raise RuntimeError("The installed Binance client has no Spot OCO endpoint")
            oco = create_oco(oco_params)
            if not isinstance(oco, dict):
                raise RuntimeError("Binance returned an invalid OCO response")
        except Exception as oco_error:
            logger.error("Binance OCO creation failed: %s", type(oco_error).__name__)
            self._recover_unprotected_position(exchange, symbol, filled_quantity, order, oco_error)

        order_reports = oco.get("orderReports") or []
        take_profit_order_id = next(
            (
                report.get("orderId")
                for report in order_reports
                if report.get("type") == "LIMIT_MAKER"
            ),
            None,
        )
        stop_loss_order_id = next(
            (
                report.get("orderId")
                for report in order_reports
                if report.get("type") in ("STOP_LOSS", "STOP_LOSS_LIMIT")
            ),
            None,
        )
        order_list_id = oco.get("orderListId", oco.get("listOrderId"))

        return {
            "status": "SUCCESS",
            "symbol": symbol,
            "entry": {
                "type": "MARKET",
                "status": "FILLED",
                "average_price": order.get("average") or order.get("price") or entry_price,
                "executed_quantity": filled_quantity,
                "quote_amount": quote_amount,
            },
            "take_profit": {
                "price": take_profit,
                "status": "ACTIVE",
                "order_id": take_profit_order_id,
            },
            "stop_loss": {
                "price": stop_loss,
                "status": "ACTIVE",
                "order_id": stop_loss_order_id,
            },
            "protection": {"type": "OCO", "status": "ACTIVE"},
            "binance_order_ids": {
                "entry_order": order.get("id"),
                "oco_order": order_list_id,
                "take_profit_order": take_profit_order_id,
                "stop_loss_order": stop_loss_order_id,
            },
        }

    def _recover_unprotected_position(
        self,
        exchange: Any,
        symbol: str,
        quantity: float,
        entry_order: dict[str, Any],
        oco_error: Exception,
    ) -> NoReturn:
        try:
            close_order = exchange.create_market_sell_order(symbol, quantity)
        except Exception as close_error:
            logger.critical(
                "Trade position is unprotected; manual recovery required "
                "(entry=%s, OCO=%s, close=%s)",
                entry_order.get("id"),
                type(oco_error).__name__,
                type(close_error).__name__,
            )
            raise TradeExecutionError(
                "OCO_ORDER_FAILED",
                "OCO protection and automatic position closure both failed; manual action is required",
                503,
                status="RECOVERY_REQUIRED",
                details={
                    "entry_order_id": entry_order.get("id"),
                    "manual_action_required": True,
                },
            ) from close_error

        raise TradeExecutionError(
            "OCO_ORDER_FAILED",
            "OCO protection failed; the position was closed with a market sell",
            503,
            status="RECOVERY_REQUIRED",
            details={
                "entry_order_id": entry_order.get("id"),
                "closed_order_id": close_order.get("id"),
                "manual_action_required": False,
            },
        ) from oco_error

    @staticmethod
    def _validate_request(
        data: dict[str, Any],
    ) -> tuple[str, str, float, float, float, float, float | None]:
        raw_symbol = data.get("symbol")
        if not isinstance(raw_symbol, str) or not raw_symbol.strip():
            raise TradeExecutionError(
                "MISSING_FIELD", "Symbol is required", details={"offended_parameter": "symbol"}
            )

        symbol_input = raw_symbol.strip().upper().replace("/", "")
        quote = config.DEFAULT_QUOTE.upper()
        if not symbol_input.endswith(quote) or len(symbol_input) <= len(quote):
            raise TradeExecutionError(
                "INVALID_SYMBOL",
                f"Symbol must be a trading pair with quote currency {quote}",
                details={"offended_parameter": "symbol"},
            )
        exchange_symbol = symbol_input
        symbol = f"{symbol_input[:-len(quote)]}/{quote}"

        entry_price = TradeExecutionService._request_number(data, "entry_price")
        quote_amount = TradeExecutionService._request_number(data, "amount")
        take_profit = TradeExecutionService._request_number(data, "take_profit")
        stop_loss = TradeExecutionService._request_number(data, "stop_loss")
        raw_sl_limit = data.get("sl_limit")
        sl_limit = (
            TradeExecutionService._request_number(data, "sl_limit")
            if raw_sl_limit is not None
            else None
        )

        if take_profit <= entry_price:
            raise TradeExecutionError(
                "INVALID_PRICE_RELATION",
                "Take profit must be greater than entry price",
                details={"offended_parameter": "take_profit"},
            )
        if stop_loss >= entry_price:
            raise TradeExecutionError(
                "INVALID_PRICE_RELATION",
                "Stop loss must be less than entry price",
                details={"offended_parameter": "stop_loss"},
            )
        if sl_limit is not None and sl_limit >= stop_loss:
            raise TradeExecutionError(
                "INVALID_SL_LIMIT",
                "Stop-loss limit price must be less than stop-loss trigger price",
                details={"offended_parameter": "sl_limit"},
            )
        return symbol, exchange_symbol, entry_price, quote_amount, take_profit, stop_loss, sl_limit

    @staticmethod
    def _request_number(data: dict[str, Any], field: str) -> float:
        value = data.get(field)
        if isinstance(value, bool):
            value = None
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = float("nan")
        if not math.isfinite(number) or number <= 0:
            raise TradeExecutionError(
                "INVALID_FIELD",
                f"{field} must be a positive finite number",
                details={"offended_parameter": field},
            )
        return number

    @staticmethod
    def _positive_number(
        value: Any,
        label: str,
        error_code: str,
        http_status: int,
    ) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = float("nan")
        if not math.isfinite(number) or number <= 0:
            raise TradeExecutionError(error_code, f"Could not determine {label}", http_status)
        return number

    @staticmethod
    def _free_balance(wallet: dict[str, Any], asset: str) -> float:
        balances = wallet.get("balances")
        if not isinstance(balances, list):
            raise TradeExecutionError(
                "WALLET_UNAVAILABLE", "Wallet response did not contain balances", 502
            )
        for balance in balances:
            if isinstance(balance, dict) and str(balance.get("asset", "")).upper() == asset:
                try:
                    free = float(balance.get("free", 0))
                except (TypeError, ValueError) as error:
                    raise TradeExecutionError(
                        "WALLET_UNAVAILABLE", "Wallet returned an invalid free balance", 502
                    ) from error
                if not math.isfinite(free) or free < 0:
                    raise TradeExecutionError(
                        "WALLET_UNAVAILABLE", "Wallet returned an invalid free balance", 502
                    )
                return free
        return 0.0
