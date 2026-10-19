# filepath: mcp_integration/server.py
"""
MCP Server — exposes trading analysis tools via Model Context Protocol.

Run with: python -m mcp_integration.server
Or as stdio: python -m mcp_integration.server stdio
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer
from mcp.server.stdio import stdio_server

from config import API_PORT, MCP_PORT
from services.analysis_service import init_analysis_service, get_analysis_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instance
_analysis_service = None


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
        """
        Analyze a coin using all 7 bots and return aggregated signal.

        Args:
            symbol: Trading symbol (e.g., "BTC", "BTCUSDT", "ETH")
            timeframe: Timeframe for analysis (1m, 5m, 15m, 1h, 4h, 1d)

        Returns:
            AggregatedSignal with final_signal, confidence, bot breakdown
        """
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
        """
        Get raw indicator values without bot analysis.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe

        Returns:
            Dictionary of indicator values (rsi, macd, mfi, adx, etc.)
        """
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
        """
        Get raw OHLCV market data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Number of candles to return

        Returns:
            List of candles with open, high, low, close, volume
        """
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
        """Get list of supported trading pairs."""
        service = get_analysis_service()
        return {"symbols": service.get_supported_symbols()}

    @server.tool(
        name="get_supported_timeframes",
        title="Get Supported Timeframes",
        description="Get supported timeframes with descriptions",
    )
    async def get_supported_timeframes() -> Dict[str, Any]:
        """Get supported timeframes."""
        service = get_analysis_service()
        return {"timeframes": service.get_supported_timeframes()}

    # Placeholder tools for future tickets (04, 05)
    @server.tool(
        name="open_trade",
        title="Open Trade",
        description="Open a new trade with dynamic SL/TP (placeholder - not implemented yet)",
    )
    async def open_trade(symbol: str, side: str, entry_price: float, sl: float, tp: float) -> Dict[str, Any]:
        return {"error": "Not implemented yet - see Ticket 04"}

    @server.tool(
        name="close_trade",
        title="Close Trade",
        description="Close an open trade (placeholder - not implemented yet)",
    )
    async def close_trade(trade_id: str, reason: str = "manual") -> Dict[str, Any]:
        return {"error": "Not implemented yet - see Ticket 04"}

    @server.tool(
        name="get_open_trades",
        title="Get Open Trades",
        description="Get all currently open trades (placeholder - not implemented yet)",
    )
    async def get_open_trades() -> Dict[str, Any]:
        return {"error": "Not implemented yet - see Ticket 04"}

    @server.tool(
        name="get_trade_history",
        title="Get Trade History",
        description="Get historical trades with P&L stats (placeholder - not implemented yet)",
    )
    async def get_trade_history(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        return {"error": "Not implemented yet - see Ticket 04"}

    @server.tool(
        name="set_risk_limit",
        title="Set Risk Limit",
        description="Set maximum daily loss limit (placeholder - not implemented yet)",
    )
    async def set_risk_limit(max_daily_loss_eur: float) -> Dict[str, Any]:
        return {"error": "Not implemented yet - see Ticket 05"}

    @server.tool(
        name="get_portfolio",
        title="Get Portfolio",
        description="Get portfolio status including capital, daily P&L, open trades (placeholder - not implemented yet)",
    )
    async def get_portfolio() -> Dict[str, Any]:
        return {"error": "Not implemented yet - see Ticket 05"}

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

    # Run MCP server
    await run_stdio()


if __name__ == "__main__":
    asyncio.run(main())