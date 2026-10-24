"""API dependencies.

FastAPI dependency injection for services and repositories.
"""

from __future__ import annotations

from fastapi import Depends

from backend.container import get_container


def get_analysis_service():
    """Dependency injection for AnalysisService via DI container."""
    container = get_container()
    return container.get("analysis_service")


def get_trade_service():
    """Dependency injection for trade executor via DI container."""
    container = get_container()
    return container.get("trade_executor")


def get_portfolio_service():
    """Dependency injection for PortfolioService via DI container."""
    container = get_container()
    return container.get("portfolio_service")


def get_risk_service():
    """Dependency injection for RiskService via DI container."""
    container = get_container()
    return container.get("risk_service")