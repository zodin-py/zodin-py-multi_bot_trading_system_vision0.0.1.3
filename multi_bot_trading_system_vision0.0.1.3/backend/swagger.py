"""OpenAPI schema generation for the Flask API."""

import re
from typing import Any


QUERY_PARAMETERS = {
    "api_price": [
        {"name": "coin", "required": True, "description": "Coin symbol"},
    ],
    "api_coin_candles": [
        {"name": "timeframe", "required": False, "description": "Candle timeframe"},
        {
            "name": "limit",
            "required": False,
            "description": "Maximum candles to return",
            "type": "integer",
        },
    ],
    "api_indicators": [
        {"name": "coin", "required": True, "description": "Coin symbol"},
        {"name": "tf", "required": False, "description": "Indicator timeframe"},
    ],
    "api_get_trades": [
        {
            "name": "limit",
            "required": False,
            "description": "Maximum trades to return",
            "type": "integer",
        },
    ],
}

REQUEST_BODIES: dict[str, dict[str, Any]] = {
    "api_coin_select": {
        "properties": {
            "timeframe": {"type": "string", "example": "5m"},
        },
    },
    "api_settings": {
        "properties": {
            "symbol": {"type": "string", "example": "BTCUSDC"},
            "timeframe": {"type": "string", "example": "1h"},
        },
    },
    "api_rag_chat": {
        "required": ["question"],
        "properties": {
            "question": {"type": "string", "example": "Summarize recent data"},
            "history": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "assistant"]},
                        "content": {"type": "string"},
                    },
                    "required": ["role", "content"],
                },
            },
            "top_k": {"type": "integer", "default": 5},
        },
    },
    "api_rag_search": {
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "example": "Bitcoin"},
            "top_k": {"type": "integer", "default": 10},
        },
    },
    "api_analysis_run": {
        "required": ["symbol"],
        "properties": {
            "symbol": {"type": "string", "example": "BTCUSDT"},
            "timeframe": {"type": "string", "default": "1h"},
            "mode": {"type": "string", "default": "current"},
            "selected": {"type": "array", "items": {"type": "object"}},
        },
    },
    "api_manual_stop": {
        "properties": {
            "reason": {"type": "string", "example": "Manueller Stop"},
        },
    },
    "trade_api.execute_trade": {
        "required": ["symbol", "entry_price", "amount", "take_profit", "stop_loss"],
        "properties": {
            "symbol": {"type": "string", "example": "BTCUSDT"},
            "entry_price": {"type": "number", "example": 95000},
            "amount": {"type": "number", "example": 100},
            "take_profit": {"type": "number", "example": 97000},
            "stop_loss": {"type": "number", "example": 94000},
            "sl_limit": {"type": "number", "example": 93800},
        },
    },
}


def build_openapi_spec(app) -> dict[str, Any]:
    """Build an OpenAPI document from registered API routes."""
    paths: dict[str, dict[str, Any]] = {}
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/"):
            continue

        path = re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", rule.rule)
        endpoint = app.view_functions[rule.endpoint]
        summary = (endpoint.__doc__ or endpoint.__name__).strip().splitlines()[0]
        path_item = paths.setdefault(path, {})

        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            operation: dict[str, Any] = {
                "operationId": f"{endpoint.__name__}_{method.lower()}",
                "summary": summary,
                "responses": {
                    "200": {"description": "JSON response"},
                    "default": {"description": "Error response"},
                },
            }
            parameters = [
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
                for name in sorted(rule.arguments)
            ]
            parameters.extend(
                {
                    "name": parameter["name"],
                    "in": "query",
                    "required": parameter["required"],
                    "description": parameter["description"],
                    "schema": {"type": parameter.get("type", "string")},
                }
                for parameter in QUERY_PARAMETERS.get(rule.endpoint, [])
            )
            if parameters:
                operation["parameters"] = parameters

            body = (
                REQUEST_BODIES.get(rule.endpoint)
                if method in {"POST", "PUT", "PATCH"}
                else None
            )
            if body:
                operation["requestBody"] = {
                    "required": bool(body.get("required")),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": body.get("required", []),
                                "properties": body["properties"],
                            },
                        },
                    },
                }
            path_item[method.lower()] = operation

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Multi-Bot Trading System API",
            "version": "1.0.0",
            "description": (
                "Interaktive API-Dokumentation. Achtung: Trade- und Hourly-Endpunkte "
                "koennen Orders ausloesen. Nur im korrekt konfigurierten Testnet testen."
            ),
        },
        "servers": [{"url": "/"}],
        "paths": paths,
    }
