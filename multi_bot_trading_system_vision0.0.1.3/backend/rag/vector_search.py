"""
Vector Search Module

Implements semantic/vector search using embeddings for the RAG system.
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .rag_config import default_config


class VectorSearch:
    """Semantic vector search using numpy for similarity computation."""

    def __init__(self, embeddings: Optional[np.ndarray] = None,
                 index_data: Optional[List[Dict[str, Any]]] = None):
        self.embeddings = embeddings  # numpy array of shape (n_docs, dim)
        self.index_data = index_data or []  # List of document metadata
        self.dim: int = 0

        if embeddings is not None:
            self.dim = embeddings.shape[1] if embeddings.ndim == 2 else 0

    def add_embeddings(self, embeddings: np.ndarray, index_data: List[Dict[str, Any]]):
        """Add embeddings and associated data to the search index."""
        if self.embeddings is None:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

        self.index_data.extend(index_data)
        self.dim = self.embeddings.shape[1]

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search for top-k similar documents using cosine similarity."""
        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        # Compute similarities between query and all documents
        similarities = np.array([self.cosine_similarity(query_embedding, emb)
                               for emb in self.embeddings])

        # Return top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    def get_nearest(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """Get nearest neighbors with full document information."""
        matches = self.search(query_embedding, top_k=top_k)
        results = []

        for idx, score in matches:
            if 0 <= idx < len(self.index_data):
                results.append({
                    "document": self.index_data[idx],
                    "similarity": score,
                    "rank": len(results) + 1,
                })

        return results

    def get_statistics(self) -> Dict[str, int]:
        """Return basic vector index statistics."""
        num_vectors = len(self.embeddings) if self.embeddings is not None else 0
        return {
            "num_vectors": num_vectors,
            "embedding_dimension": self.dim,
        }