"""Analysis Engine — coordinates all analysis modules.

The Analysis Engine is the core coordinator that:
1. Receives selected analyzers from the frontend
2. Validates analyzer IDs
3. Loads corresponding modules from the Registry
4. Loads required configurations
5. Creates AnalysisContext from OHLCV candle data
6. Executes each analyzer independently
7. Standardizes and collects results
8. Ensures error isolation (one analyzer failure doesn't stop others)

This matches Section 7 of the Spect.md - the Analysis Engine.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.analyzers.registry import AnalyzerRegistry
from backend.analyzers.base_analyzer import (
    AnalysisContext,
    AnalysisResult,
)


logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Core analysis engine that coordinates all analysis modules.

    The engine follows the workflow described in Section 7 of the Spect.md:
    1. Frontend sends selected analyzers
    2. Backend validates analyzer IDs
    3. Backend loads modules from Registry
    4. Backend loads configurations
    5. Backend creates AnalysisContext
    6. Each analyzer runs independently
    7. Results are standardized and collected
    8. Results are returned to frontend

    Error isolation: A failure in one analyzer does not stop others.
    """

    def __init__(self, registry: Optional[AnalyzerRegistry] = None) -> None:
        self.registry = registry or AnalyzerRegistry()
        self._cache: Dict[str, Any] = {}  # For shared computations

    def set_registry(self, registry: AnalyzerRegistry) -> None:
        """Set the analyzer registry."""
        self.registry = registry

    def run_analysis(
        self,
        symbol: str,
        timeframe: str,
        mode: str,
        selected: List[Dict[str, Any]],
        all_candles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Run analysis on the given symbol/timeframe with selected analyzers.

        This is the main entry point for the Analysis Engine.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            timeframe: Candle timeframe (e.g., '1h')
            mode: 'current' or 'history'
            selected: List of analyzer selection dicts from frontend
                      each with: analyzer_id, mode (optional), config (optional)
            all_candles: List of all available candle dicts

        Returns:
            Dict with analysis results organized by analyzer
        """
        # Step 1: Validate analyzer IDs
        validated_selected = self._validate_and_prepare_selectors(
            selected, symbol, timeframe
        )

        if not validated_selected:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "mode": mode,
                "results": {},
                "errors": "No valid analyzers selected",
            }

        # Step 2: Determine the latest closed candle index
        latest_closed_index = len(all_candles) - 1 if all_candles else 0

        # Step 4: Execute each analyzer independently
        results: Dict[str, Any] = {}
        errors: List[Dict[str, Any]] = []

        for selector in validated_selected:
            analyzer_id = selector.get("analyzer_id")
            config = selector.get("config", {})
            analyzer_mode = selector.get("mode", mode)  # Per-element mode overrides

            try:
                # Get the analyzer from registry
                analyzer = self.registry.get(analyzer_id)
                if analyzer is None:
                    error_msg = f"Analyzer '{analyzer_id}' not found in registry"
                    errors.append({
                        "analyzer_id": analyzer_id,
                        "error": error_msg,
                    })
                    results[analyzer_id] = {
                        "status": "error",
                        "error": error_msg,
                        "signals": [],
                        "series": [],
                    }
                    continue

                # Run the analyzer
                context = AnalysisContext(
                    symbol=symbol,
                    timeframe=timeframe,
                    candles=all_candles,
                    mode=analyzer_mode,
                    latest_closed_index=latest_closed_index,
                )
                result: AnalysisResult = analyzer.analyze(
                    context=context,
                    config=config,
                )

                # Convert to dict for JSON serialization
                results[analyzer_id] = {
                    "status": result.status,
                    "analyzer_id": result.analyzer_id,
                    "symbol": result.symbol,
                    "timeframe": result.timeframe,
                    "mode": result.mode,
                    "signals": result.signals,
                    "series": result.series,
                }

                # Log any analyzer errors but continue
                if result.status == "error":
                    logger.warning(
                        f"Analyzer {analyzer_id} returned error: "
                        f"{result.signals if result.signals else 'no signals'}"
                    )

            except Exception as e:
                error_msg = f"Unexpected error running analyzer {analyzer_id}: {e}"
                errors.append({
                    "analyzer_id": analyzer_id,
                    "error": error_msg,
                })
                logger.error(error_msg, exc_info=True)
                results[analyzer_id] = {
                    "status": "error",
                    "error": error_msg,
                    "signals": [],
                    "series": [],
                }

        # Step 5: Return collected results
        output = {
            "symbol": symbol,
            "timeframe": timeframe,
            "mode": mode,
            "results": results,
        }

        if errors:
            output["errors"] = errors

        return output

    def _validate_and_prepare_selectors(
        self,
        selected: List[Dict[str, Any]],
        symbol: str,
        timeframe: str,
    ) -> List[Dict[str, Any]]:
        """Validate and prepare analyzer selectors from frontend.

        Args:
            selected: List of analyzer selection dicts from frontend
            symbol: Trading symbol
            timeframe: Candle timeframe

        Returns:
            List of validated selectors, or empty list if none valid
        """
        validated: List[Dict[str, Any]] = []

        for selector in selected:
            analyzer_id = selector.get("analyzer_id", "").strip()

            if not analyzer_id:
                logger.warning("Selector without analyzer_id, skipping")
                continue

            # Check if analyzer exists in registry
            if not self.registry.exists(analyzer_id):
                logger.warning(f"Analyzer '{analyzer_id}' not found, skipping")
                continue

            # Validate configuration
            analyzer = self.registry.get(analyzer_id)
            config = selector.get("config", {})
            validation_errors = analyzer.validate_config(config) if analyzer else []

            if validation_errors:
                logger.warning(
                    f"Analyzer '{analyzer_id}' config validation failed: "
                    f"{validation_errors}"
                )
                # Still run with validated config (may fail in analyze)

            validated.append({
                "analyzer_id": analyzer_id,
                "config": config,
                "mode": selector.get("mode", ""),  # Will be overridden by per-element mode
            })

        return validated

    def get_available_analyzers(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available analyzers categorized by type.

        Returns:
            Dict with categories as keys and lists of analyzer metadata as values
        """
        return {
            "indicators": self.registry.list_indicators(),
            "patterns": self.registry.list_patterns(),
            "strategies": self.registry.list_strategies(),
        }

    def get_analyzer_metadata(self, analyzer_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific analyzer.

        Args:
            analyzer_id: The analyzer ID (e.g., 'indicator.rsi', 'pattern.hammer')

        Returns:
            Metadata dict, or None if not found
        """
        return self.registry.get_metadata(analyzer_id)