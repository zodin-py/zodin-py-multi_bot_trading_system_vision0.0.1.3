"""
DI Container — Dependency Injection Container

Creates all shared services exactly once via constructor injection.
Replaces all global singleton getters (get_analysis_service, get_trade_service, etc).

Usage:
    container = get_container()
    services = container.build()
    analysis_service = services['analysis_service']
    trade_executor = services['trade_executor']
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple, TypeVar

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protocol definitions (service interfaces)
# ---------------------------------------------------------------------------


class MarketDataProvider(Protocol):
    """Protocol: market data access."""

    def get_current_price(self, symbol: str) -> float: ...
    def get_ohlcv(
        self, symbol: str, timeframe: str, periods: int = 50
    ) -> Optional[Tuple[List[float], ...]]: ...
    def get_candles(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_stale(self, symbol: str, timeframe: str) -> bool: ...


class IndicatorProviderProtocol(Protocol):
    """Protocol: indicator computation and access."""

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]: ...
    def get_ohlcv(
        self, symbol: str, timeframe: str, periods: int = 50
    ) -> Optional[Tuple[List[float], ...]]: ...
    def is_stale(self, symbol: str, timeframe: str) -> bool: ...


class IndicatorCalculatorProtocol(Protocol):
    """Protocol: indicator calculation engine."""

    def compute(
        self,
        symbol: str,
        timeframe: str,
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
    ) -> Optional[Any]: ...
    def get_cached(self, symbol: str, timeframe: str) -> Optional[Any]: ...


class TradeRepositoryProtocol(Protocol):
    """Protocol: trade persistence layer."""

    def save(self, trade: Dict[str, Any]) -> str: ...
    def get_open_trades(self) -> List[Dict[str, Any]]: ...
    def get_trade_history(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...
    def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]: ...
    def update_status(self, trade_id: str, status: str, **kwargs) -> bool: ...


class PortfolioServiceProtocol(Protocol):
    """Protocol: portfolio management."""

    def get_portfolio(self) -> Dict[str, Any]: ...
    def get_daily_pnl(self) -> float: ...
    def reset_daily_pnl(self) -> bool: ...


class RiskServiceProtocol(Protocol):
    """Protocol: risk management."""

    def check_daily_loss_limit(self) -> bool: ...
    def calculate_position_size(
        self, entry_price: float, stop_loss: float, capital: float, risk_percent: float
    ) -> float: ...
    def get_risk_parameters(self) -> Dict[str, Any]: ...
    def is_trading_halted(self) -> bool: ...


class AnalysisServiceProtocol(Protocol):
    """Protocol: analysis orchestration."""

    async def initialize(self) -> None: ...
    async def shutdown(self) -> None: ...
    def analyze_coin(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]: ...
    def get_indicators(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]: ...
    def get_market_data(self, symbol: str, timeframe: str = "1h", limit: int = 50) -> Dict[str, Any]: ...


class BrainProtocol(Protocol):
    """Protocol: signal aggregation."""

    def aggregate_signals(
        self, symbol: str, timeframe: str, provider: IndicatorProviderProtocol
    ) -> Any: ...
    def get_bot_probabilities(
        self, symbol: str, timeframe: str, provider: IndicatorProviderProtocol
    ) -> Dict[str, float]: ...


class TradeExecutorProtocol(Protocol):
    """Protocol: trade execution."""

    def open_trade(
        self,
        symbol: str,
        timeframe: str,
        signal: Any,
        entry_price: float,
        **kwargs
    ) -> Optional[Any]: ...
    def close_trade(self, trade_id: str, reason: str = 'manual', current_price: float = 0.0) -> Optional[Any]: ...
    def get_open_trades(self) -> List[Any]: ...
    def get_trade_history(self, start=None, end=None) -> List[Any]: ...
    def get_performance_stats(self, start=None, end=None) -> Dict[str, Any]: ...
    def get_portfolio(self) -> Dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Placeholder implementations
# ---------------------------------------------------------------------------


class PlaceholderMarketData:
    """Placeholder: raises NotImplementedError until ticket 04 implements real MarketData."""

    def __init__(self, cache: Any = None, ttl_sec: int = 300):
        self.ttl_sec = ttl_sec
        self._current_prices: Dict[str, float] = {}

    def get_current_price(self, symbol: str) -> float:
        raise NotImplementedError("MarketData not implemented yet (ticket 04)")

    def get_ohlcv(
        self, symbol: str, timeframe: str, periods: int = 50
    ) -> Optional[Tuple[List[float], ...]]:
        raise NotImplementedError("MarketData not implemented yet (ticket 04)")

    def get_candles(self, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("MarketData not implemented yet (ticket 04)")

    def start(self) -> None:
        logger.info("PlaceholderMarketData.start() called")

    def stop(self) -> None:
        logger.info("PlaceholderMarketData.stop() called")

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        return False


class PlaceholderIndicatorCalculator:
    """Placeholder: raises NotImplementedError until ticket 05 implements real calculator."""

    def compute(
        self,
        symbol: str,
        timeframe: str,
        opens: List[float],
        highs: List[float],
        lows: List[float],
        closes: List[float],
        volumes: List[float],
    ) -> Optional[Any]:
        raise NotImplementedError("IndicatorCalculator not implemented yet (ticket 05)")

    def get_cached(self, symbol: str, timeframe: str) -> Optional[Any]:
        return None


class PlaceholderIndicatorProvider:
    """Placeholder: bridges MarketData + IndicatorCalculator."""

    def __init__(
        self,
        market_data: MarketDataProvider,
        calculator: IndicatorCalculatorProtocol,
    ):
        self.market_data = market_data
        self.calculator = calculator

    def get_indicators(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("IndicatorProvider not implemented yet (ticket 05)")

    def get_ohlcv(
        self, symbol: str, timeframe: str, periods: int = 50
    ) -> Optional[Tuple[List[float], ...]]:
        return self.market_data.get_ohlcv(symbol, timeframe, periods)

    def is_stale(self, symbol: str, timeframe: str) -> bool:
        return self.market_data.is_stale(symbol, timeframe)


class PlaceholderTradeRepository:
    """Placeholder: raises NotImplementedError until ticket 07 implements trade persistence."""

    def save(self, trade: Dict[str, Any]) -> str:
        raise NotImplementedError("TradeRepository not implemented yet (ticket 07)")

    def get_open_trades(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("TradeRepository not implemented yet (ticket 07)")

    def get_trade_history(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("TradeRepository not implemented yet (ticket 07)")

    def get_trade(self, trade_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("TradeRepository not implemented yet (ticket 07)")

    def update_status(self, trade_id: str, status: str, **kwargs) -> bool:
        raise NotImplementedError("TradeRepository not implemented yet (ticket 07)")


class PlaceholderPortfolioService:
    """Placeholder: raises NotImplementedError until ticket 08 implements portfolio tracking."""

    def get_portfolio(self) -> Dict[str, Any]:
        raise NotImplementedError("PortfolioService not implemented yet (ticket 08)")

    def get_daily_pnl(self) -> float:
        raise NotImplementedError("PortfolioService not implemented yet (ticket 08)")

    def reset_daily_pnl(self) -> bool:
        raise NotImplementedError("PortfolioService not implemented yet (ticket 08)")


class PlaceholderRiskService:
    """Placeholder: raises NotImplementedError until ticket 09 implements risk management."""

    def check_daily_loss_limit(self) -> bool:
        raise NotImplementedError("RiskService not implemented yet (ticket 09)")

    def calculate_position_size(
        self, entry_price: float, stop_loss: float, capital: float, risk_percent: float
    ) -> float:
        raise NotImplementedError("RiskService not implemented yet (ticket 09)")

    def get_risk_parameters(self) -> Dict[str, Any]:
        raise NotImplementedError("RiskService not implemented yet (ticket 09)")

    def is_trading_halted(self) -> bool:
        raise NotImplementedError("RiskService not implemented yet (ticket 09)")


class PlaceholderBrain:
    """Placeholder: raises NotImplementedError until ticket 06 implements signal aggregation."""

    def aggregate_signals(
        self, symbol: str, timeframe: str, provider: IndicatorProviderProtocol
    ) -> Any:
        raise NotImplementedError("Brain not implemented yet (ticket 06)")

    def get_bot_probabilities(
        self, symbol: str, timeframe: str, provider: IndicatorProviderProtocol
    ) -> Dict[str, float]:
        raise NotImplementedError("Brain not implemented yet (ticket 06)")


class PlaceholderTradeExecutor:
    """Placeholder: raises NotImplementedError until ticket 10 implements execution."""

    def __init__(self, capital: float = 10000.0, simulated: bool = False):
        self.capital = capital
        self.simulated = simulated

    def open_trade(
        self,
        symbol: str,
        timeframe: str,
        signal: Any,
        entry_price: float,
        **kwargs
    ) -> Optional[Any]:
        raise NotImplementedError("TradeExecutor not implemented yet (ticket 10)")

    def close_trade(self, trade_id: str, reason: str = 'manual', current_price: float = 0.0) -> Optional[Any]:
        raise NotImplementedError("TradeExecutor not implemented yet (ticket 10)")

    def get_open_trades(self) -> List[Any]:
        raise NotImplementedError("TradeExecutor not implemented yet (ticket 10)")

    def get_trade_history(self, start=None, end=None) -> List[Any]:
        raise NotImplementedError("TradeExecutor not implemented yet (ticket 10)")

    def get_performance_stats(self, start=None, end=None) -> Dict[str, Any]:
        raise NotImplementedError("TradeExecutor not implemented yet (ticket 10)")

    def get_portfolio(self) -> Dict[str, Any]:
        raise NotImplementedError("TradeExecutor not implemented yet (ticket 10)")


class PlaceholderAnalysisService:
    """Placeholder: raises NotImplementedError until tickets 04-06 are implemented."""

    def __init__(
        self,
        market_data: MarketDataProvider,
        calculator: IndicatorCalculatorProtocol,
        provider: IndicatorProviderProtocol,
        brain: BrainProtocol,
    ):
        self.market_data = market_data
        self.calculator = calculator
        self.provider = provider
        self.brain = brain

    async def initialize(self) -> None:
        raise NotImplementedError("AnalysisService not implemented yet (ticket 06)")

    async def shutdown(self) -> None:
        raise NotImplementedError("AnalysisService not implemented yet (ticket 06)")

    def analyze_coin(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        raise NotImplementedError("AnalysisService not implemented yet (ticket 06)")

    def get_indicators(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        raise NotImplementedError("AnalysisService not implemented yet (ticket 06)")

    def get_market_data(self, symbol: str, timeframe: str = "1h", limit: int = 50) -> Dict[str, Any]:
        raise NotImplementedError("AnalysisService not implemented yet (ticket 06)")


# ---------------------------------------------------------------------------
# Container class
# ---------------------------------------------------------------------------


class Container:
    """
    DI Container: creates all shared services exactly once via constructor injection.

    Services instantiated:
    - market_data: MarketData (ccxt REST + WebSocket + DuckDB cache)
    - indicator_calculator: IndicatorCalculator (pandas_ta / ta-lib)
    - indicator_provider: IndicatorProviderAdapter (bridges market_data + calculator)
    - analysis_service: AnalysisService (orchestrates bots + brain)
    - brain: Brain (signal aggregation)
    - trade_executor: TradeExecutor (order placement via ccxt)
    - trade_repository: TradeRepository (persistence layer)
    - portfolio_service: PortfolioService (position tracking)
    - risk_service: RiskService (daily loss limits, position sizing)
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}

    def build(self) -> Dict[str, Any]:
        """
        Build and return all service instances.

        Returns:
            Dict mapping service names to instances.
        """
        if self._services:
            return self._services

        # 1. Core infrastructure services
        market_data = PlaceholderMarketData()
        indicator_calculator = PlaceholderIndicatorCalculator()
        indicator_provider = PlaceholderIndicatorProvider(market_data, indicator_calculator)

        # 2. Domain services (placeholders until tickets 04-10)
        trade_repository = PlaceholderTradeRepository()
        portfolio_service = PlaceholderPortfolioService()
        risk_service = PlaceholderRiskService()
        brain = PlaceholderBrain()
        trade_executor = PlaceholderTradeExecutor()
        analysis_service = PlaceholderAnalysisService(
            market_data=market_data,
            calculator=indicator_calculator,
            provider=indicator_provider,
            brain=brain,
        )

        # Wire services
        self._services = {
            'market_data': market_data,
            'indicator_calculator': indicator_calculator,
            'indicator_provider': indicator_provider,
            'analysis_service': analysis_service,
            'brain': brain,
            'trade_executor': trade_executor,
            'trade_repository': trade_repository,
            'portfolio_service': portfolio_service,
            'risk_service': risk_service,
        }

        logger.info("Container built with all services")
        return self._services

    def get(self, name: str) -> Any:
        """Get a service by name."""
        services = self.build()
        if name not in services:
            raise KeyError(f"Service '{name}' not found in container")
        return services[name]

    def register(self, name: str, service: Any) -> None:
        """Register a service override (for testing or replacement)."""
        self._services[name] = service

    def reset(self) -> None:
        """Clear all services (useful for testing)."""
        self._services.clear()


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------


_container: Optional[Container] = None


def get_container() -> Container:
    """
    Get or create the singleton Container instance.

    Returns:
        Container: The singleton DI container.
    """
    global _container
    if _container is None:
        _container = Container()
    return _container


# ---------------------------------------------------------------------------
# FastAPI dependency providers (for later use with Depends())
# ---------------------------------------------------------------------------


async def get_market_data() -> MarketDataProvider:
    """FastAPI dependency: provides MarketData instance."""
    return get_container().get('market_data')


async def get_indicator_provider() -> IndicatorProviderProtocol:
    """FastAPI dependency: provides IndicatorProvider instance."""
    return get_container().get('indicator_provider')


async def get_analysis_service() -> AnalysisServiceProtocol:
    """FastAPI dependency: provides AnalysisService instance."""
    return get_container().get('analysis_service')


async def get_brain() -> BrainProtocol:
    """FastAPI dependency: provides Brain instance."""
    return get_container().get('brain')


async def get_trade_executor() -> TradeExecutorProtocol:
    """FastAPI dependency: provides TradeExecutor instance."""
    return get_container().get('trade_executor')


async def get_trade_repository() -> TradeRepositoryProtocol:
    """FastAPI dependency: provides TradeRepository instance."""
    return get_container().get('trade_repository')


async def get_portfolio_service() -> PortfolioServiceProtocol:
    """FastAPI dependency: provides PortfolioService instance."""
    return get_container().get('portfolio_service')


async def get_risk_service() -> RiskServiceProtocol:
    """FastAPI dependency: provides RiskService instance."""
    return get_container().get('risk_service')


# ---------------------------------------------------------------------------
# MCP server dependency providers
# ---------------------------------------------------------------------------


def mcp_get_market_data() -> MarketDataProvider:
    """MCP tool dependency: provides MarketData instance."""
    return get_container().get('market_data')


def mcp_get_analysis_service() -> AnalysisServiceProtocol:
    """MCP tool dependency: provides AnalysisService instance."""
    return get_container().get('analysis_service')


def mcp_get_trade_executor() -> TradeExecutorProtocol:
    """MCP tool dependency: provides TradeExecutor instance."""
    return get_container().get('trade_executor')


# ---------------------------------------------------------------------------
# Main entry point for testing
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    container = get_container()
    services = container.build()

    print("=" * 60)
    print("DI Container - Service Instances")
    print("=" * 60)
    for name, service in services.items():
        print(f"  {name:25s} -> {type(service).__name__}")
    print("=" * 60)
    print(f"\nTotal services: {len(services)}")
    print(f"Container singleton: {id(container)}")
    print(f"get_container() returns same: {id(get_container())}")