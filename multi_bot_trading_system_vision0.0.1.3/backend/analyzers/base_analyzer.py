"""Base analyzer interface — all analysis modules must implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AnalysisContext:
    """Context passed to each analyzer."""

    def __init__(
        self,
        symbol: str,
        timeframe: str,
        candles: list,
        mode: str,
        latest_closed_index: int,
        start_timestamp: int | None = None,
        end_timestamp: int | None = None,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.candles = candles
        self.mode = mode
        self.latest_closed_index = latest_closed_index
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp


class AnalysisResult:
    """Standardized result returned by each analyzer."""

    def __init__(
        self,
        analyzer_id: str,
        symbol: str,
        timeframe: str,
        mode: str,
        signals: Optional[List[Dict[str, Any]]] = None,
        series: Optional[List[Dict[str, Any]]] = None,
        status: str = "success",
    ) -> None:
        self.analyzer_id = analyzer_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.mode = mode
        self.signals = signals or []
        self.series = series or []
        self.status = status


class BaseAnalyzer(ABC):
    """Base interface that all analysis modules must implement.

    Each analyzer provides:
    - Metadata about itself (name, category, description, icon)
    - Default configuration
    - Configuration validation
    - Analysis execution

    The analyze() method receives an AnalysisContext and returns an AnalysisResult.
    """

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return analyzer metadata including name, category, description, and icon."""
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration for this analyzer."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate analyzer configuration.

        Returns a list of error messages (empty if valid).
        """
        pass

    @abstractmethod
    def analyze(self, context: AnalysisContext, config: Dict[str, Any]) -> AnalysisResult:
        """Run the analysis on the given context with the given config.

        Must be thread-safe and not modify shared state.
        """
        pass