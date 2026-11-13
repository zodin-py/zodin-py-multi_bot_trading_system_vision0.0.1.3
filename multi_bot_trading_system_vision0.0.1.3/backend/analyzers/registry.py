"""Analyzer Registry — manages all available analysis modules.

Tasks:
- Analyzer registration
- Analyzer lookup by ID
- Listing all available analyzers
- Category filtering
- Metadata provisioning
- Existence checking
- Duplicate ID prevention

Analyzer IDs follow the pattern:
- indicator.ema, indicator.rsi, indicator.macd
- pattern.hammer, pattern.doji, pattern.bullish_engulfing
- strategy.custom.12345
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from backend.analyzers.base_analyzer import BaseAnalyzer, AnalysisResult

logger = logging.getLogger(__name__)


class AnalyzerRegistry:
    """Registry managing all available analysis modules."""

    def __init__(self) -> None:
        self._analyzers: Dict[str, BaseAnalyzer] = {}
        self._categories: Dict[str, Set[str]] = {}  # category -> set of analyzer IDs

    def register(self, analyzer: BaseAnalyzer, force: bool = False) -> bool:
        """Register an analyzer module.

        Args:
            analyzer: The analyzer instance to register
            force: If True, overwrite existing analyzer with same ID

        Returns:
            True if registration succeeded, False if ID already exists and force=False
        """
        analyzer_id = analyzer.get_metadata().get("id", "")
        if not analyzer_id:
            # Derive ID from class name
            class_name = type(analyzer).__name__.lower()
            # Remove "analyzer" suffix if present
            if class_name.endswith("analyzer"):
                class_name = class_name[:-len("analyzer")]
            analyzer_id = class_name

        if analyzer_id in self._analyzers and not force:
            logger.warning(f"Analyzer ID '{analyzer_id}' already registered. Use force=True to overwrite.")
            return False

        metadata = analyzer.get_metadata()
        category = metadata.get("category", "unknown")

        # Remove from old category if re-registering
        if analyzer_id in self._analyzers:
            old_category = self._get_analyzer_category(analyzer_id)
            if old_category and old_category in self._categories:
                self._categories[old_category].discard(analyzer_id)

        self._analyzers[analyzer_id] = analyzer

        # Add to category
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(analyzer_id)

        logger.info(f"Registered analyzer: {analyzer_id} (category: {category})")
        return True

    def _get_analyzer_category(self, analyzer_id: str) -> Optional[str]:
        """Get the category for a registered analyzer ID."""
        for category, ids in self._categories.items():
            if analyzer_id in ids:
                return category
        return None

    def get(self, analyzer_id: str) -> Optional[BaseAnalyzer]:
        """Get an analyzer by ID.

        Args:
            analyzer_id: The analyzer ID (e.g., 'indicator.rsi', 'pattern.hammer')

        Returns:
            The analyzer instance, or None if not found
        """
        return self._analyzers.get(analyzer_id)

    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered analyzers with their metadata.

        Returns:
            List of analyzer metadata dicts
        """
        results = []
        for analyzer_id, analyzer in self._analyzers.items():
            metadata = analyzer.get_metadata()
            metadata["id"] = analyzer_id
            results.append(metadata)
        return results

    def list_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List analyzers filtered by category.

        Args:
            category: The category name to filter by

        Returns:
            List of analyzer metadata dicts in the given category
        """
        analyzer_ids = self._categories.get(category, set())
        results = []
        for analyzer_id in analyzer_ids:
            analyzer = self._analyzers.get(analyzer_id)
            if analyzer:
                metadata = analyzer.get_metadata()
                metadata["id"] = analyzer_id
                results.append(metadata)
        return results

    def exists(self, analyzer_id: str) -> bool:
        """Check if an analyzer ID is registered.

        Args:
            analyzer_id: The analyzer ID to check

        Returns:
            True if the analyzer is registered
        """
        return analyzer_id in self._analyzers

    def get_metadata(self, analyzer_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific analyzer.

        Args:
            analyzer_id: The analyzer ID

        Returns:
            Metadata dict, or None if not found
        """
        analyzer = self._analyzers.get(analyzer_id)
        if analyzer:
            return analyzer.get_metadata()
        return None

    def list_strategies(self) -> List[Dict[str, Any]]:
        """List only strategy-type analyzers.

        Returns:
            List of strategy analyzer metadata dicts
        """
        return self.list_by_category("strategy")

    def list_indicators(self) -> List[Dict[str, Any]]:
        """List only indicator-type analyzers.

        Returns:
            List of indicator analyzer metadata dicts
        """
        return self.list_by_category("indicator")

    def list_patterns(self) -> List[Dict[str, Any]]:
        """List only candlestick pattern-type analyzers.

        Returns:
            List of pattern analyzer metadata dicts
        """
        return self.list_by_category("pattern")

    def get_analyzer_ids_by_category(self, category: str) -> List[str]:
        """Get analyzer IDs filtered by category.

        Args:
            category: The category name

        Returns:
            List of analyzer IDs in the given category
        """
        return list(self._categories.get(category, set()))