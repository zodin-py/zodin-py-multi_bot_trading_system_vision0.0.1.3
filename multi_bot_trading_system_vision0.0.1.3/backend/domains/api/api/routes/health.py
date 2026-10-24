"""Health check API routes.

FastAPI endpoints for health monitoring.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}