"""FastAPI app factory — domain-specific route registration.

Creates the FastAPI application with all domain routes registered.
Replace the old monolithic api/server.py by importing routes from
domains/api instead of keeping everything in one file.

Run with: python -m backend.main
Or:   uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.container import get_container

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    container = get_container()

    app = FastAPI(
        title="Multi-Bot Trading System API",
        description="REST API for multi-bot crypto trading analysis and execution",
        version="0.1.0",
    )

    # CORS middleware — allow Angular dev server (port 4200) to call API (port 8000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and register domain-specific route modules
    from backend.domains.api.routes import health
    from backend.domains.api.routes import analysis
    from backend.domains.api.routes import trades
    from backend.domains.api.routes import portfolio

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
    app.include_router(trades.router, prefix="/api/v1", tags=["trades"])
    app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])

    # Root health check (no prefix)
    @app.get("/health", include_in_schema=False)
    async def root_health():
        """Root health check."""
        return {"status": "ok"}

    logger.info("FastAPI app created with domain-specific routes")
    return app


# Allow running as: python -m backend.main
app = create_app()