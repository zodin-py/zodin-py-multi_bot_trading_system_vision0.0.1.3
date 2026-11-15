"""RAG monitor for retrieval and API latency tracking.

Tracks retrieval latency, LLM API latency, and provides diagnostics
for the RAG system. Implements the rag_monitor module from the
Spec.md architecture document.
"""

import logging
import time
from collections import OrderedDict
from typing import Dict, List, Optional, Any

import numpy as np

from backend.rag.rag_service import RagService, RagServiceError

logger = logging.getLogger(__name__)


class RetrievalMetrics:
    """Metrics for a single retrieval operation."""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.query: str = ""
        self.top_k: int = 0
        self.status: str = ""
        self.keyword_results: int = 0
        self.vector_results: int = 0
        self.combined_results: int = 0
        self.context_characters: int = 0
        self.retrieval_ms: float = 0.0
        self.llm_ms: float = 0.0
        self.sources_count: int = 0
        self.insufficient_information: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "top_k": self.top_k,
            "status": self.status,
            "keyword_results": self.keyword_results,
            "vector_results": self.vector_results,
            "combined_results": self.combined_results,
            "context_characters": self.context_characters,
            "retrieval_ms": round(self.retrieval_ms, 2),
            "llm_ms": round(self.llm_ms, 2),
            "sources_count": self.sources_count,
            "insufficient_information": self.insufficient_information,
        }


class RagMonitor:
    """Monitor for tracking RAG system performance and diagnostics."""

    def __init__(self, rag_service: RagService, max_history: int = 100):
        self.rag_service = rag_service
        self.max_history = max_history
        self._analyses: OrderedDict[str, dict] = OrderedDict()

    def record_analysis(self, request_id: str, analysis: dict) -> None:
        """Record an analysis result from a chat request."""
        with self._lock():
            self._analyses[request_id] = analysis
            # Keep only the last max_history entries
            if len(self._analyses) > self.max_history:
                self._analyses.popitem(last=False)

    def get_recent(self, n: int = 10) -> List[dict]:
        """Get the last n analysis records."""
        with self._lock():
            items = list(self._analyses.items())[-n:]
            return [value for _, value in items]

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics from recorded analyses."""
        with self._lock():
            analyses = list(self._analyses.values())

            if not analyses:
                return {
                    "total_requests": 0,
                    "average_retrieval_ms": 0,
                    "average_llm_ms": 0,
                    "status_distribution": {},
                    "insufficient_rate": 0,
                }

            total = len(analyses)
            avg_retrieval = sum(a.get("analysis", {}).get("retrieval_ms", 0) for a in analyses) / total
            avg_llm = sum(a.get("llm_ms", 0) for a in analyses) / total

            # Status distribution
            status_dist: Dict[str, int] = {}
            for a in analyses:
                status = a.get("status", "unknown")
                status_dist[status] = status_dist.get(status, 0) + 1

            # Insufficient information rate
            insufficient = sum(1 for a in analyses if a.get("insufficient_information", False))
            insufficient_rate = insufficient / total if total > 0 else 0

            return {
                "total_requests": total,
                "average_retrieval_ms": round(avg_retrieval, 2),
                "average_llm_ms": round(avg_llm, 2),
                "status_distribution": status_dist,
                "insufficient_rate": round(insufficient_rate, 4),
            }

    def _lock(self):
        """Return a context manager for the thread lock."""
        return self.rag_service._lock  # type: ignore


# Global monitor instance (lazy initialization)
_monitor: Optional[RagMonitor] = None


def get_monitor(rag_service: RagService) -> RagMonitor:
    """Get or create the global RagMonitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = RagMonitor(rag_service)
    return _monitor