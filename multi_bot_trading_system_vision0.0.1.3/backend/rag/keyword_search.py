"""
Keyword Search Module

Implements BM25-style keyword search for the RAG system.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from .rag_config import default_config


class BM25Index:
    """BM25 keyword search index implementation."""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.avg_doc_len: float = 0.0
        self.tokenized_docs: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.vocab: Set[str] = set()

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the BM25 index."""
        for doc in documents:
            text = doc.get("text", doc.get("content", str(doc)))
            metadata = doc.get("metadata", {})
            self.documents.append({"text": text, "metadata": metadata})

        # Tokenize all documents
        self.tokenized_docs = []
        for doc in self.documents:
            tokens = self._tokenize(doc["text"])
            self.tokenized_docs.append(tokens)

        # Compute average document length
        doc_lens = [len(tokens) for tokens in self.tokenized_docs]
        self.avg_doc_len = sum(doc_lens) / len(doc_lens) if doc_lens else 0.0

        # Compute IDF (Inverse Document Frequency)
        self._compute_idf()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words, removing punctuation."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Filter out short tokens
        tokens = [t for t in tokens if len(t) > 2]
        return tokens

    def _compute_idf(self):
        """Compute Inverse Document Frequency for all terms."""
        num_docs = len(self.tokenized_docs)
        if num_docs == 0:
            return

        # Count how many documents contain each term
        doc_freq: Dict[str, int] = Counter()
        for tokens in self.tokenized_docs:
            unique_terms = set(tokens)
            for term in unique_terms:
                doc_freq[term] += 1

        # Compute IDF using smoothing
        self.idf = {}
        self.vocab = set()
        for term, df in doc_freq.items():
            self.idf[term] = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            self.vocab.add(term)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search for top-k documents matching the query."""
        if not self.tokenized_docs or not self.idf:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Compute BM25 scores for each document
        scores: List[float] = []
        for doc_tokens in self.tokenized_docs:
            score = self._bm25_score(query_tokens, doc_tokens)
            scores.append(score)

        # Return top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(idx, scores[idx]) for idx in top_indices]

    def _bm25_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """Compute BM25 score for a single document."""
        doc_len = len(doc_tokens)
        if doc_len == 0:
            return 0.0

        score = 0.0
        doc_freq: Dict[str, int] = Counter(doc_tokens)

        for term in query_tokens:
            if term not in self.idf:
                continue

            idf = self.idf[term]
            freq = doc_freq.get(term, 0)

            # BM25 formula
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len) if self.avg_doc_len > 0 else 1

            if denominator > 0:
                score += idf * numerator / denominator

        return score

    def get_statistics(self) -> Dict[str, Any]:
        """Return index statistics."""
        return {
            "num_documents": len(self.documents),
            "vocab_size": len(self.vocab),
            "avg_doc_len": self.avg_doc_len,
            "num_terms_in_idf": len(self.idf),
        }


class KeywordSearch:
    """Keyword search interface combining BM25 with result formatting."""

    def __init__(self, bm25_index: BM25Index):
        self.bm25 = bm25_index

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search and return formatted results."""
        matches = self.bm25.search(query, top_k=top_k)
        results = []

        for idx, score in matches:
            doc = self.bm25.documents[idx]
            results.append({
                "document": doc,
                "score": score,
                "rank": len(results) + 1,
                "method": "bm25",
            })

        return results