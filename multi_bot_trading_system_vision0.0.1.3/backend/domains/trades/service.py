"""Trades domain service.

Coordinates trade management operations.
"""

from backend.domains.execution.service import ExecutionService as TradesService

__all__ = ["TradesService"]