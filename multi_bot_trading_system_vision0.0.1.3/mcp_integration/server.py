# filepath: mcp_integration/server.py
"""
MCP Server — exposes trading analysis tools via Model Context Protocol.

Run with: python -m mcp_integration.server
Or as stdio: python -m mcp_integration.server stdio
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.stdio import stdio_server

from config import API_PORT, MCP_PORT
from services.analysis_service import init_analysis_service, get_analysis_service
from services.trade_service import get_trade_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
_analysis_service = None
_trade_service = None


def create_mcp_server() -> MCPServer:
    """Create and configure the MCP server with all tools."""
    server = MCPServer(
        name="multi-bot-trading-system",
        title="Multi-Bot Crypto Trading System",
        description="MCP server for multi-bot crypto trading analysis and execution",
        version="0.1.0",
    )

    @server.tool(
        name="analyze_coin",
        title="Analyze Coin",
        description="Run full multi-bot analysis for a single coin symbol and timeframe",
    )
    async def analyze_coin(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        service = get_analysis_service()
        try:
            result = service.analyze_coin(symbol, timeframe)
            return result
        except Exception as e:
            logger.error(f"analyze_coin error: {e}")
            return {"error": str(e)}

    @server.tool(
        name="get_indicators",
        title="Get Indicators",
        description="Get pre-computed technical indicator values for a symbol/timeframe",
    )
    async def get_indicators(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        service = get_analysis_service()
        try:
            result = service.get_indicators(symbol, timeframe)
            return result
        except Exception as e:
            logger.error(f"get_indicators error: {e}")
            return {"error": str(e)}

    @server.tool(
        name="get_market_data",
        title="Get Market Data",
        description="Get OHLCV candle data for a symbol/timeframe",
    )
    async def get_market_data(symbol: str, timeframe: str = "1h", limit: int = 50) -> Dict[str, Any]:
        service = get_analysis_service()
        try:
            result = service.get_market_data(symbol, timeframe, limit)
            return result
        except Exception as e:
            logger.error(f"get_market_data error: {e}")
            return {"error": str(e)}

    @server.tool(
        name="get_supported_symbols",
        title="Get Supported Symbols",
        description="Get list of all supported trading symbols",
    )
    async def get_supported_symbols() -> Dict[str, Any]:
        service = get_analysis_service()
        return {"symbols": service.get_supported_symbols()}

    @server.tool(
        name="get_supported_timeframes",
        title="Get Supported Timeframes",
        description="Get supported timeframes with descriptions",
    )
    async def get_supported_timeframes() -> Dict[str, Any]:
        service = get_analysis_service()
        return {"timeframes": service.get_supported_timeframes()}

    # ---- Trade tools (Ticket 04) ----

    @server.tool(
        name="open_trade",
        title="Open Trade",
        description="Open a new trade with dynamic SL/TP based on aggregated signal. "
                    "Requires signal confidence >= 65%. Places real order on Binance Testnet.",
    )
    async def open_trade(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Open a trade by running full analysis and executing if signal confidence >= 65%.

        Args:
            symbol: Trading symbol (e.g., "BTC", "BTCUSDT")
            timeframe: Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1d)

        Returns:
            Trade dict or error
        """
        ts = get_trade_service()
        try:
            # Run analysis to get signal
            analysis = get_analysis_service().analyze_coin(symbol, timeframe)
            final_signal = analysis.get('final_signal')
            confidence = analysis.get('confidence', 0)

            if confidence < 65:
                return {
                    'error': f'Signal confidence {confidence:.1f}% below threshold 65%',
                    'final_signal': final_signal,
                    'confidence': confidence,
                }

            # Map signal type
            signal_map = {'buy': 'buy', 'sell': 'sell'}
            signal_type = signal_map.get(final_signal, 'hold')
            if signal_type == 'hold':
                return {'error': 'No actionable signal (hold)', 'final_signal': final_signal}

            result = ts.open_trade(symbol, timeframe, signal_type)
            return result

        except Exception as e:
            logger.error(f"open_trade error: {e}")
            return {"error": str(e)}

    @server.tool(
        name="close_trade",
        title="Close Trade",
        description="Close an open trade at the current market price.",
    )
    async def close_trade(trade_id: str, reason: str = "manual") -> Dict[str, Any]:
        ts = get_trade_service()
        try:
            result = ts.close_trade(trade_id, reason=reason)
            return result
        except Exception as e:
            logger.error(f"close_trade error: {e}")
            return {"error": str(e)}

    @server.tool(
        name="get_open_trades",
        title="Get Open Trades",
        description="Get all currently open trades with entry, SL, TP, and side.",
    )
    async def get_open_trades() -> Dict[str, Any]:
        ts = get_trade_service()
        return {"trades": ts.get_open_trades(), "count": len(ts.get_open_trades())}

    @server.tool(
        name="get_trade_history",
        title="Get Trade History",
        description="Get historical trades with P&L stats. Optional date filters.",
    )
    async def get_trade_history(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        ts = get_trade_service()
        return ts.get_trade_history(start_date=start_date, end_date=end_date)

    @server.tool(
        name="get_portfolio",
        title="Get Portfolio",
        description="Get portfolio status including capital, daily P&L, open trades, halt status.",
    )
    async def get_portfolio() -> Dict[str, Any]:
        ts = get_trade_service()
        return ts.get_portfolio()

    @server.tool(
        name="set_risk_limit",
        title="Set Risk Limit",
        description="Set maximum daily loss limit (trading halts when reached).",
    )
    async def set_risk_limit(max_daily_loss_eur: float) -> Dict[str, Any]:
        """Update MAX_DAILY_LOSS from config at runtime."""
        import config
        config.MAX_DAILY_LOSS = max_daily_loss_eur
        ts = get_trade_service()
        return {"success": True, "current_limit": max_daily_loss_eur}

    return server


async def run_stdio():
    """Run MCP server over stdio (for Claude Code integration)."""
    logger.info("Starting MCP server on stdio...")
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


async def main():
    """Main entry point."""
    # Initialize analysis service
    await init_analysis_service()
    logger.info("Analysis service initialized")

    # Initialize trade service (uses same market_data + calculator)
    from execution.executor import TradeExecutor
    from services.trade_service import init_trade_service

    svc = get_analysis_service()
    executor = TradeExecutor()
    init_trade_service(svc.market_data, executor, svc.provider)
    logger.info("Trade service initialized")

    # Run MCP server
    await run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
