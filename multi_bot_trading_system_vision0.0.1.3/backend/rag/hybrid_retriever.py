"""Combine BM25 and local vector search using weighted Reciprocal Rank Fusion."""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .keyword_search import BM25Index
from .vector_search import VectorSearch


class HybridRetriever:
    """Combine keyword and vector result rankings using weighted RRF."""

    def __init__(
        self,
        bm25_index: BM25Index,
        vector_search: VectorSearch,
        keyword_weight: float = 0.5,
        vector_weight: float = 0.5,
    ):
        self.bm25_index = bm25_index
        self.vector_search = vector_search
        self.keyword_weight = keyword_weight
        self.vector_weight = vector_weight
        self.rrf_k = 60

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        query_embedding: Optional[np.ndarray] = None,
    ) -> List[Dict[str, Any]]:
        keyword_matches = [
            match for match in self.bm25_index.search(query, top_k=top_k * 3)
            if match[1] > 0
        ]
        vector_matches = []
        if query_embedding is not None:
            vector_matches = [
                match for match in self.vector_search.search(
                    query_embedding, top_k=top_k * 3
                )
                if match[1] > 0
            ]

        scores: Dict[int, float] = {}
        for weight, matches in (
            (self.keyword_weight, keyword_matches),
            (self.vector_weight, vector_matches),
        ):
            for rank, (document_id, _) in enumerate(matches, start=1):
                scores[document_id] = scores.get(document_id, 0.0) + (
                    weight / (self.rrf_k + rank)
                )

        results = []
        for document_id, score in sorted(
            scores.items(), key=lambda item: item[1], reverse=True
        )[:top_k]:
            if document_id >= len(self.bm25_index.documents):
                continue
            results.append({
                "document": self.bm25_index.documents[document_id],
                "score": score,
                "rank": len(results) + 1,
                "method": "hybrid",
            })
        return results

    def rrf_fuse(
        self,
        keyword_ranks: Dict[int, int],
        vector_ranks: Dict[int, int],
    ) -> List[Tuple[int, float]]:
        fused_scores: Dict[int, float] = {}
        for ranks, weight in (
            (keyword_ranks, self.keyword_weight),
            (vector_ranks, self.vector_weight),
        ):
            for document_id, rank in ranks.items():
                fused_scores[document_id] = fused_scores.get(document_id, 0.0) + (
                    weight / (self.rrf_k + rank)
                )
        return sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
