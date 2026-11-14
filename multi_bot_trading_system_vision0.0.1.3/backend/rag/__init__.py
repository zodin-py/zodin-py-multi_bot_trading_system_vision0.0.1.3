"""RAG (Retrieval-Augmented Generation) Module for the Multi-Bot Trading System.

This module provides a complete RAG system that integrates with the existing
multi-bot trading infrastructure, combining keyword search, vector search,
and hybrid retrieval using Reciprocal Rank Fusion.
"""

from .rag_config import RagConfig, default_config
from .data_loader import DataLoader
from .data_validator import DataValidator
from .embedding_service import EmbeddingService
from .keyword_search import BM25Index, KeywordSearch
from .vector_search import VectorSearch
from .hybrid_retriever import HybridRetriever
from .rag_service import RagService

__all__ = [
    "RagService",
    "RagConfig",
    "default_config",
    "DataLoader",
    "DataValidator",
    "EmbeddingService",
    "BM25Index",
    "KeywordSearch",
    "VectorSearch",
    "HybridRetriever",
]